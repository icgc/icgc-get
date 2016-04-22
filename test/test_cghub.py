from lib.cli import icgc_download_client
from argparse import Namespace
from conftest import file_test, get_info


class TestCGHubMethods():

    def test_cghub(self, config, data_dir):
        args = Namespace(config=config, file=['a337c425-4314-40c6-a40a-a444781bd1b7'], manifest=None, output=data_dir,
                         repo='cghub')
        icgc_download_client.call_client(args)
        file_info = get_info(data_dir, 'a337c425-4314-40c6-a40a-a444781bd1b7/G28034.MDA-MB-361.1.bam')
        assert file_test(file_info, 5159984257)

    def test_cghub_double(self, config, data_dir):
        args = Namespace(config=config,
                         file=['a452b625-74f6-40b5-90f8-7fe6f32b89bd', 'a105a6ec-7cc3-4c3b-a99f-af29de8a7caa'],
                         manifest=None, output=data_dir,repo='cghub')
        icgc_download_client.call_client(args)
        file1_info = get_info(data_dir, 'a105a6ec-7cc3-4c3b-a99f-af29de8a7caa/C836.BICR_18.2.bam')
        file2_info = get_info(data_dir, 'a452b625-74f6-40b5-90f8-7fe6f32b89bd/C836.PEER.1.bam')
        assert (file_test(file1_info, 8163241177) and file_test(file2_info, 8145679575))

    def test_cghub_manifest(self, config, data_dir, manifest_dir):

        args = Namespace(config=config, file=None, manifest=manifest_dir + 'manifest.xml', output=data_dir,
                         repo='cghub')
        icgc_download_client.call_client(args)
        file1_info = get_info(data_dir, 'fcfc5e01-19a3-45de-ab4b-5440f49c6340/C836.MDA-MB-436.1.bam')
        file2_info = get_info(data_dir, 'f135768c-ffdf-4743-bb62-226131776b83/C836.NCC-StC-K140.1.bam')

        assert file_test(file1_info, 5191968) and file_test(file2_info, 7864608923) 

