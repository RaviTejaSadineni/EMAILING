from datetime import UTC, datetime

from app.models.email import Email
from app.services.thread_merge_service import deterministic_groups, merge_confidence, normalize_subject


def test_subject_normalization():
    assert normalize_subject('Re: FWD: FW: Contract') == 'contract'


def test_deterministic_pregrouping_by_reply_and_subject():
    e1 = Email(message_id='<1@x>', subject='Contract A', from_address='a@x.com', to_addresses=['b@x.com'])
    e2 = Email(message_id='<2@x>', subject='Re: Contract A', from_address='b@x.com', to_addresses=['a@x.com'], in_reply_to='<1@x>')
    e3 = Email(message_id='<3@x>', subject='Other', from_address='c@x.com', to_addresses=['d@x.com'])

    groups = deterministic_groups([e1, e2, e3])
    sizes = sorted(len(group) for group in groups)
    assert sizes == [1, 2]


def test_merge_confidence_scoring():
    now = datetime.now(UTC)
    g1 = [Email(message_id='<a>', subject='MSA Draft', from_address='a@x.com', to_addresses=['b@x.com'], date=now)]
    g2 = [Email(message_id='<b>', subject='Re: MSA Draft', from_address='b@x.com', to_addresses=['a@x.com'], date=now)]
    score = merge_confidence(g1, g2)
    assert 0 <= score <= 1
    assert score > 0.7
