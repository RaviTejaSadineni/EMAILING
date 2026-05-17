import mailbox
from email.message import EmailMessage

from app.services.mbox_parser import MboxParser


def _build_mbox(path):
    mbox = mailbox.mbox(path)

    msg1 = EmailMessage()
    msg1['Message-ID'] = '<m1@example.com>'
    msg1['Subject'] = 'Simple Subject'
    msg1['From'] = 'Alice <alice@example.com>'
    msg1['To'] = 'Bob <bob@example.com>'
    msg1['Date'] = 'Mon, 20 Jan 2025 10:00:00 +0000'
    msg1.set_content('plain body')
    mbox.add(msg1)

    msg2 = EmailMessage()
    msg2['Message-ID'] = '<m2@example.com>'
    msg2['Subject'] = '=?utf-8?b?VGVzdCDinJQ=?='
    msg2['From'] = 'Carol <carol@example.com>'
    msg2['To'] = 'Dave <dave@example.com>'
    msg2['Cc'] = 'Eva <eva@example.com>'
    msg2['References'] = '<m0@example.com> <m1@example.com>'
    msg2['In-Reply-To'] = '<m1@example.com>'
    msg2.set_content('text body')
    msg2.add_alternative('<p>html body</p>', subtype='html')
    msg2.add_attachment(b'contract-v1', maintype='application', subtype='pdf', filename='contract.pdf')
    mbox.add(msg2)

    mbox.flush()


def test_mbox_parser_extracts_fields_and_attachments(tmp_path):
    path = tmp_path / 'sample.mbox'
    _build_mbox(path)

    parser = MboxParser(path)
    emails = list(parser.iter_emails())

    assert len(emails) == 2
    first = emails[0]
    assert first.subject == 'Simple Subject'
    assert first.from_address == 'alice@example.com'
    assert first.to_addresses == ['bob@example.com']

    second = emails[1]
    assert second.subject
    assert second.in_reply_to == '<m1@example.com>'
    assert second.references == ['<m0@example.com>', '<m1@example.com>']
    assert second.body_text
    assert second.body_html
    assert len(second.attachments) == 1
    assert second.attachments[0].filename == 'contract.pdf'
    assert second.attachments[0].size == len(b'contract-v1')


def test_mbox_parser_skips_malformed_messages(tmp_path):
    path = tmp_path / 'broken.mbox'
    with path.open('wb') as handle:
        handle.write(b'From test@example.com Mon Jan  1 00:00:00 2025\n')
        handle.write(b'\xff\xfe\xfa\n\n')

    parser = MboxParser(path)
    assert list(parser.iter_emails()) == []
