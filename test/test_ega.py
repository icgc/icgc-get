from argparse import Namespace
from lib.cli import icgc_download_client
from conftest import file_test, get_info
from lib.cli import icgc_download_client


class TestEGAMethods():

    def test_ega(self, config, data_dir):
        args = Namespace(config=config, file=['EGAD00001001847'], manifest=None, output=data_dir, repo='ega')
        icgc_download_client.call_client(args)
        file1_info = get_info(data_dir, '_EGAR00001385154_4Cseq_single-end_HD-MB03_TGFBR1_sequence.fastq.gz')
        file2_info = get_info(data_dir, '_EGAR00001385153_4Cseq_single-end_HD-MB03_SMAD9_sequence.fastq.gz')
        assert (file_test(file1_info, 323699429), file_test(file2_info, 447127561))

    def test_ega_file(self, config, data_dir):
        args = Namespace(config=config, file=['EGAF00000112559'], manifest=None, output=data_dir, repo='ega')
        icgc_download_client.call_client(args)
        file_info = get_info(data_dir, '_methylationCEL_CLL-174.CEL')
        assert (file_test(file_info, 5556766))


