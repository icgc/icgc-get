from icgcget.clients.icgc import icgc_api

def test_multiple_files():
    icgc_api.get_metadata_bulk(["FI250134", "FI99990"], "https://staging.dcc.icgc.org/api/v1/repository/")
