import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from test_core import request,profile,event,START
from test_message_extraction_contract import task,response
from buy_or_wait.evidence_integration import forecast_with_evidence
from buy_or_wait.fx import RateBook
from buy_or_wait.message_extraction import parse_output
from buy_or_wait.load import load_dataset
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'code/evaluation'))
from message_extract import tasks
from message_results import evaluate

class MessageIntegrationTests(unittest.TestCase):
    def test_real_corpus_selection_is_once_per_message_across_cohorts(self):
        root=Path(__file__).resolve().parents[1]/'dataset'
        batches=[list(tasks(load_dataset(root,name))) for name in ('requests.csv','sample_requests.csv')]
        self.assertEqual([len(rows) for rows in batches],[198,17])
        ids=[m.message_id for rows in batches for q,m,t in rows]
        self.assertEqual(len(ids),len(set(ids)))

    def test_hypothetical_candidate_pipeline_cannot_increase_cash(self):
        from test_message_extraction_contract import fact
        t=task()
        batch=parse_output(response([fact(certainty='HYPOTHETICAL')]),t)
        r=forecast_with_evidence(profile(),request(),(),RateBook(()),(t.source,),(batch,))
        self.assertTrue(r.forecast.complete,r.forecast.issues)
        self.assertFalse(r.normalized.amendments)
        self.assertFalse(r.forecast.cash_flows)

    def test_no_fact_resolves_source_but_failed_empty_batch_does_not(self):
        t=task('Good morning.')
        batch=parse_output(response([],outcome='NO_FACT'),t)
        complete=forecast_with_evidence(profile(),request(),(),RateBook(()),(t.source,),(batch,)).forecast
        failed=forecast_with_evidence(profile(),request(),(),RateBook(()),(t.source,),()).forecast
        self.assertTrue(complete.complete);self.assertFalse(failed.complete)

    def test_report_only_evaluates_selected_request_cohort(self):
        data=SimpleNamespace(selected_requests=(request(),),requests={'unselected':object()},
                             profiles={'person':profile()},events_by_user={},rates=(),messages_by_user={},images_by_user={})
        r=evaluate(data,{})
        self.assertEqual(len(r['requests']),1)
        self.assertEqual(r['summary']['complete_after'],1)
