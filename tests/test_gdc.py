from argparse import Namespace

from icgcget import cli
from conftest import file_test, get_info


class TestGDCMethods():

    def test_gdc(self, config, data_dir):

        args = Namespace(config=config, file=['f483ad78-b092-4d10-9afb-eccacec9d9dc'], manifest=None,output=data_dir,
                         repo='gdc')
        cli.call_client(args)
        file_info = get_info(data_dir,
                             'f483ad78-b092-4d10-9afb-eccacec9d9dc/TCGA-CH-5763-01A-11D-1572-02_AC1JWAACXX' +
                             '---TCGA-CH-5763-11A-01D-1572-02_AC1JWAACXX---Segment.tsv')
        assert file_test(file_info, 1483)

    def test_gdc_double(self, config, data_dir):
        args = Namespace(config=config,
                         file=['2c759eb8-7ee0-43f5-a008-de4317ab8c70', 'a6b2f1ff-5c71-493c-b65d-e344ed29b7bb'],
                         manifest=None, output=data_dir, repo='gdc')
        cli.call_client(args)
        file1_info = get_info(data_dir, '2c759eb8-7ee0-43f5-a008-de4317ab8c70/14-3-3_beta-R-V_GBL11066140.tif')
        file2_info = get_info(data_dir, 'a6b2f1ff-5c71-493c-b65d-e344ed29b7bb/14-3-3_beta-R-V_GBL11066140.txt')
        assert file_test(file1_info, 6261580) and file_test(file2_info, 1399430)

    def test_gdc_manifest(self, config, data_dir, manifest_dir):
        args = Namespace(config=config, file=None,
                         manifest=manifest_dir + 'gdc_manifest_1677e1a1e443d44e301239c10c7dc5d29c7f2658.txt',
                         output=data_dir, repo='gdc')
        cli.call_client(args)
        file1_info = get_info(data_dir, '48016dd8-6033-4d73-8c85-f6eb1896e465/14-3-3_beta-R-V_GBL11066140.txt')
        file2_info = get_info(data_dir, '71014f3d-6c29-4977-a5fa-568cbcbf8787/14-3-3_beta-R-V_GBL1114584.tif')
        file3_info = get_info(data_dir, 'cf1f6b6b-d6d8-4b0b-9ace-a344e088875e/14-3-3_beta-R-V_GBL1114584.txt')
        assert file_test(file1_info, 1399430) and file_test(file2_info, 6182680) and file_test(file3_info, 1400580)


