"""Run: python -m unittest discover -s tests -v"""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Thread
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from unittest import TestCase, mock
import json
from backend.config import CITIES, IST
from backend.database import Database
from backend.models import WeatherReading, risk_level
from backend.predictor import LinearTrendModel
from backend.providers import DemoProvider, OpenMeteoProvider
from backend.server import create_server
from backend.service import HeatwaveService


class ProjectTests(TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.db = Database(Path(self.temp.name) / 'test.db')
        self.service = HeatwaveService(self.db)

    def tearDown(self):
        self.temp.cleanup()

    def test_exact_warning_boundaries(self):
        self.assertEqual([risk_level(t) for t in [34.9,35,39.9,40,44.9,45]], ['Normal','Watch','Watch','High','High','Severe'])

    def test_invalid_and_nonfinite_values(self):
        for t,h in [(61,50),(30,-1),(30,101),(float('nan'),50),(30,float('inf'))]:
            with self.assertRaises(ValueError):
                WeatherReading('dombivli',datetime.now(IST).isoformat(),t,h,'manual')

    def test_demo_observations_and_forecasts_are_separate(self):
        data=self.service.snapshot('dombivli')
        self.assertEqual(len(data['history']),24)
        self.assertEqual(len(data['forecast']),24)
        self.assertEqual(data['peak'],41.1)
        self.assertEqual(data['prediction']['samples'],7)
        self.assertTrue(all(row['recorded_at']>data['current']['recorded_at'] for row in data['forecast']))

    def test_manual_reading_persists_without_contaminating_model(self):
        before=self.service.snapshot('dombivli')['prediction']
        self.service.add_manual({'city_id':'dombivli','temperature':55,'humidity':45})
        reopened=HeatwaveService(Database(self.db.path))
        self.assertEqual(len(reopened.database.readings('dombivli','manual')),1)
        self.assertEqual(reopened.snapshot('dombivli')['prediction'],before)

    def test_acknowledgement_persists_and_cascading_delete(self):
        row=self.service.add_manual({'city_id':'mumbai','temperature':46,'humidity':40})
        with self.db.connect() as db:
            alert=dict(db.execute('SELECT * FROM alerts WHERE reading_id=?',(row['id'],)).fetchone())
        self.assertTrue(self.db.acknowledge(alert['id']))
        self.assertTrue(self.db.delete_manual(row['id']))
        with self.db.connect() as db:
            self.assertIsNone(db.execute('SELECT * FROM alerts WHERE reading_id=?',(row['id'],)).fetchone())

    def test_refresh_is_idempotent_and_keeps_reviewed_status(self):
        initial=self.service.snapshot('dombivli')
        first=initial['alerts'][0]['id']
        self.db.acknowledge(first)
        self.service.refresh('dombivli','demo')
        self.assertEqual(len(self.db.readings('dombivli','demo')),48)
        self.assertEqual(self.service.snapshot('dombivli')['alerts'][0]['acknowledged'],1)

    def test_protected_provider_rows(self):
        row=self.db.readings('dombivli','demo')[0]
        self.assertFalse(self.db.delete_manual(row['id']))

    def test_regression_known_straight_line_and_insufficient_input(self):
        start=datetime(2026,5,18,6,tzinfo=IST)
        rows=[{'recorded_at':(start+timedelta(hours=i)).isoformat(),'temperature':30+i} for i in range(7)]
        result=LinearTrendModel().predict(rows)
        self.assertEqual(result['temperature'],39)
        self.assertEqual(result['slope'],1)
        self.assertFalse(LinearTrendModel().predict(rows[:2])['available'])

    def test_live_provider_contract_with_fixture(self):
        # Validates response parsing without depending on outside network access.
        payload={'current':{'time':'2026-05-18T12:15','temperature_2m':39,'relative_humidity_2m':50},
                 'hourly':{'time':['2026-05-18T11:00','2026-05-18T13:00'],
                           'temperature_2m':[38,40],'relative_humidity_2m':[52,48]}}
        response=mock.MagicMock()
        response.__enter__.return_value.read.return_value=json.dumps(payload).encode()
        with mock.patch('backend.providers.urlopen',return_value=response):
            rows=OpenMeteoProvider().fetch(CITIES[0])
        self.assertEqual([row.kind for row in rows],['observation','forecast','observation'])
        self.assertEqual(rows[-1].recorded_at,'2026-05-18T12:15:00+05:30')

    def test_fetch_failure_does_not_erase_saved_rows(self):
        before=len(self.db.readings('dombivli'))
        with mock.patch.object(self.service.providers['live'],'fetch',side_effect=TimeoutError):
            with self.assertRaises(TimeoutError):
                self.service.refresh('dombivli','live')
        self.assertEqual(len(self.db.readings('dombivli')),before)

    def test_concurrent_writes_use_separate_connections(self):
        def insert(index):
            return self.service.add_manual({'city_id':'pune','temperature':30+index/10,'humidity':50})
        with ThreadPoolExecutor(max_workers=4) as pool:
            list(pool.map(insert,range(12)))
        self.assertEqual(len(self.db.readings('pune','manual')),12)

    def test_unknown_city_and_future_observation(self):
        with self.assertRaises(ValueError): self.service.snapshot("'; DROP TABLE cities; --")
        with self.assertRaises(ValueError):
            self.service.add_manual({'city_id':'pune','temperature':35,'humidity':60,'recorded_at':(datetime.now(IST)+timedelta(days=2)).isoformat()})

    def test_http_roundtrip_json_errors_and_static_frontend(self):
        server=create_server(0,self.service)
        thread=Thread(target=server.serve_forever,daemon=True)
        thread.start()
        base='http://127.0.0.1:'+str(server.server_port)
        try:
            with urlopen(base+'/') as response: self.assertIn(b'Heatwave overview',response.read())
            with urlopen(base+'/api/dashboard?city=mumbai&mode=demo') as response:
                self.assertEqual(json.load(response)['city']['name'],'Mumbai')
            req=Request(base+'/api/readings',data=json.dumps({'city_id':'pune','temperature':41.5,'humidity':55}).encode(),headers={'Content-Type':'application/json'})
            with urlopen(req) as response:
                self.assertEqual(response.status,201)
                row=json.load(response)
            req=Request(base+'/api/delete-reading',data=json.dumps({'id':row['id']}).encode(),headers={'Content-Type':'application/json'})
            with urlopen(req) as response: self.assertTrue(json.load(response)['ok'])
            req=Request(base+'/api/readings',data=b'{invalid',headers={'Content-Type':'application/json'})
            with self.assertRaises(HTTPError) as context: urlopen(req)
            self.assertEqual(context.exception.code,400)
            req=Request(base+'/api/readings',data=b'{}',headers={'Content-Type':'application/json','Origin':'https://example.com'})
            with self.assertRaises(HTTPError) as context: urlopen(req)
            self.assertEqual(context.exception.code,403)
        finally:
            server.shutdown(); server.server_close(); thread.join()
