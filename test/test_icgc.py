from lib.cli import icgc_download_client
from argparse import Namespace
from conftest import file_test, get_info


class TestIcgcMethods():

    def test_icgc(self, config, data_dir):
        args = Namespace(config=config, file=['a5a6d87b-e599-528b-aea0-73f5084205d5'], manifest=None,output=data_dir,
                         repo='collab')
        icgc_download_client.call_client(args)
        file_info = get_info(data_dir, 'fc447d55-95d8-0b34-e040-11ac0d483afa.embl-delly_1-0-0-preFilter.20150618' +
                             '.germline.sv.vcf.gz/a5a6d87b-e599-528b-aea0-73f5084205d5')
        file2_info = get_info(data_dir, 'fc447d55-95d8-0b34-e040-11ac0d483afa.embl-delly_1-0-0-preFilter.20150618.' +
                              'germline.sv.vcf.gz.tbi/efcb7a5c-ff36-5557-84a3-7d4aa0e416b8')
        assert (file_test(file_info, 202180) and file_test(file2_info, 21701))

    def test_icgc_manifest(self, config, data_dir, manifest_dir):

        args = Namespace(config=config, file=None, manifest=manifest_dir + 'manifest.collaboratory.1461082640538.txt',
                         output='/Users/GavinWilson/git/icgc-download-client/mnt/downloads', repo='collab')
        icgc_download_client.call_client(args)
        file1_info = get_info(data_dir, 'f37971bd-ec65-4840-8d4f-678692cee695.embl-delly_1-3-0-preFilter.20151106.' +
                              'germline.sv.vcf.gz/ec37ddf9-9ea4-5b8b-ac38-c9e415b302c4')
        file2_info = get_info(data_dir, 'f37971bd-ec65-4840-8d4f-678692cee695.embl-delly_1-3-0-preFilter' +
                               '.20151106.germline.sv.vcf.gz.tbi/6829a356-5204-5948-9505-506443ef4269')
        file3_info = get_info(data_dir, 'c9ad6b1c-baa0-45a7-b7c4-733728505b8a.broad-snowman.20151023' +
                               '.germline.sv.vcf.gz/6e6d420d-fb38-5958-b545-b6a36b52f82f')
        file4_info = get_info(data_dir, 'a78b5788-67ea-4275-931c-421bf76c5a4c.broad-snowman.20151107' +
                               '.germline.sv.vcf.gz/4862d12a-7c48-5adf-939b-be93303d9847')
        file5_info = get_info(data_dir, '6d3551d6-b5f4-4fd1-b8d7-8e5931096c19.broad-snowman.20151023.germline' +
                               '.sv.vcf.gz/965865a6-0b0c-5f83-b2f8-4b16e382b643')
        assert (file_test(file1_info, 191099) and file_test(file2_info, 20587) and file_test(file3_info, 1520928) and
                file_test(file4_info, 1381742) and file_test(file5_info, 1625731))
