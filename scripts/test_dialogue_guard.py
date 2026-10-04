#!/usr/bin/env python3
import unittest
from audit_plottr_dialogue import audit, quote_spans, rich_text


def project(text, second=None):
    cards=[{"id":1,"lineId":3,"beatId":11,"bookId":1,"description":[{"type":"paragraph","children":[{"text":text}]}]}]
    if second is not None:
        cards.append({"id":2,"lineId":3,"beatId":12,"bookId":1,"description":[{"type":"paragraph","children":[{"text":second}]}]})
    return {"lines":[{"id":3,"title":"PL-01\uff5cMain"}],"beats":{"1":{"index":{"11":{"title":"E07-S01"},"12":{"title":"E07-S02"}}}},"cards":cards}


class DialogueGuardTests(unittest.TestCase):
    def test_nested_quotes(self):
        self.assertEqual(quote_spans('\u300cA\u300eB\u300fC\u300d')[0]['quote'], '\u300cA\u300eB\u300fC\u300d')

    def test_marks_do_not_split_quote(self):
        value=[{'type':'paragraph','children':[{'text':'\u300cA'},{'text':'B','bold':True},{'text':'C\u300d'}]}]
        self.assertEqual(rich_text(value),'\u300cABC\u300d')

    def test_compatible_exact_retention(self):
        data=project('\u300cA\u300d')
        self.assertEqual(audit(data,data)['counts'],{'retained':1})

    def test_baseline_recovers_earlier_deletion(self):
        source=project('\u300cA\u300d'); previous=project('summary'); target=project('\u300cA\u300d')
        self.assertEqual(audit(source,target,baseline=previous)['counts'],{'restored':1})

    def test_unexplained_removal_blocks(self):
        r=audit(project('\u300cA\u300d'),project('summary'))
        self.assertEqual(r['unresolved_count'],1)
        self.assertTrue(r['errors'])

    def test_punctuation_change_requires_disposition(self):
        r=audit(project('\u300cA!\u300d'),project('\u300cA\u300d'))
        self.assertEqual(r['unresolved_count'],1)

    def test_duplicate_occurrences_are_counted(self):
        r=audit(project('\u300cA\u300d\u300cA\u300d'),project('\u300cA\u300d'))
        self.assertEqual(r['unresolved_count'],1)

    def test_moved_line_requires_target_and_reason(self):
        r=audit(project('\u300cA\u300d', ''),project('', '\u300cA\u300d'),decisions={'D-001-001':{'status':'moved','target_card':2,'reason':'POV placement'}})
        self.assertEqual(r['counts'],{'moved':1});self.assertFalse(r['errors'])

    def test_wrong_move_target_fails(self):
        r=audit(project('\u300cA\u300d'),project(''),decisions={'D-001-001':{'status':'moved','target_card':2,'reason':'POV'}})
        self.assertTrue(r['errors'])

    def test_adaptation_preserves_original_in_report(self):
        r=audit(project('\u300cA\u300d'),project('\u300cB\u300d'),decisions={'D-001-001':{'status':'adapted','replacement':'\u300cB\u300d','reason':'timing'}})
        self.assertEqual(r['rows'][0]['quote'],'\u300cA\u300d')
        self.assertEqual(r['counts'],{'adapted':1});self.assertFalse(r['errors'])

    def test_held_line_keeps_raw_wording(self):
        r=audit(project('\u300cA\u300d'),project(''),decisions={'D-001-001':{'status':'held','reason':'alternate plot'}})
        self.assertEqual(r['rows'][0]['quote'],'\u300cA\u300d');self.assertFalse(r['errors'])

    def test_held_line_needs_reason(self):
        r=audit(project('\u300cA\u300d'),project(''),decisions={'D-001-001':{'status':'held'}})
        self.assertTrue(r['errors'])

    def test_labels_are_explicitly_classified(self):
        r=audit(project('\u300cA\u300d'),project(''),decisions={'D-001-001':{'status':'non_dialogue','reason':'heading'}})
        self.assertEqual(r['counts'],{'non_dialogue':1})

    def test_unknown_disposition_is_flagged(self):
        r=audit(project('\u300cA\u300d'),project('\u300cA\u300d'),decisions={'D-999-001':{'status':'held','reason':'x'}})
        self.assertTrue(r['errors'])

if __name__=='__main__':
    unittest.main()
