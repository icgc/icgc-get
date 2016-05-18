import logging
import click
from tabulate import tabulate
from clients.errors import SubprocessError
from collections import OrderedDict
from clients import portal_client
from clients.ega.ega_client import EgaDownloadClient
from clients.gdc.gdc_client import GdcDownloadClient
from clients.gnos.gnos_client import GnosDownloadClient
from clients.icgc.storage_client import StorageClient
from utils import file_size, calculate_size, donor_addition, increment_types
import cli


def download(repos, fileids, manifest, output,
             cghub_access, cghub_path, cghub_transport_parallel,
             ega_access, ega_path, ega_transport_parallel, ega_udt,
             gdc_access, gdc_path, gdc_transport_parallel, gdc_udt,
             icgc_access, icgc_path, icgc_transport_file_from, icgc_transport_parallel, yes_to_all, api_url):
    logger = logging.getLogger('__log__')
    if manifest:
        if len(fileids) > 1:
            logger.warning("For download from manifest files, multiple manifest id arguments is not supported")
            raise click.BadArgumentUsage("Multiple manifest files specified.")
        portal = portal_client.IcgcPortalClient()
        manifest_json = cli.api_error_catch(portal.get_manifest_id, fileids[0], api_url, repos)
    else:

        portal = portal_client.IcgcPortalClient()
        manifest_json = cli.api_error_catch(portal.get_manifest, fileids, api_url, repos)

    if not manifest_json["unique"] or len(manifest_json["entries"]) != 1:
        cli.filter_manifest_ids(manifest_json, )
    size, object_ids = calculate_size(manifest_json)

    cli.size_check(size, yes_to_all, output)

    if 'cghub' in object_ids and object_ids['cghub']:
        cli.check_access(cghub_access, 'cghub')
        gt_client = GnosDownloadClient()
        return_code = gt_client.download(object_ids['cghub'], cghub_access, cghub_path, output,
                                         cghub_transport_parallel)
        cli.check_code('Cghub', return_code)

    if 'aws-virginia' in object_ids and object_ids['aws-virginia']:
        cli.check_access(icgc_access, 'icgc')
        icgc_client = StorageClient()
        return_code = icgc_client.download(object_ids['aws-virginia'], icgc_access, icgc_path, output,
                                           icgc_transport_parallel, file_from=icgc_transport_file_from, repo='aws')
        cli.check_code('Icgc', return_code)

    if 'ega' in object_ids and object_ids['ega']:
        cli.check_access(ega_access, 'ega')
        if ega_transport_parallel != '1':
            logger.warning("Parallel streams on the ega client may cause reliability issues and failed " +
                           "downloads.  This option is not recommended.")
        ega_client = EgaDownloadClient()
        return_code = ega_client.download(object_ids['ega'], ega_access, ega_path, output, ega_transport_parallel,
                                          ega_udt)
        cli.check_code('Ega', return_code)

    if 'collaboratory' in object_ids and object_ids['collaboratory']:
        cli.check_access(icgc_access, 'icgc')
        icgc_client = StorageClient()
        return_code = icgc_client.download(object_ids['collaboratory'], icgc_access, icgc_path, output,
                                           icgc_transport_parallel, file_from=icgc_transport_file_from, repo='collab')
        cli.check_code('Icgc', return_code)

    if 'gdc' in object_ids and object_ids['gdc']:
        cli.check_access(gdc_access, 'gdc')
        gdc_client = GdcDownloadClient()
        return_code = gdc_client.download(object_ids['gdc'], gdc_access, gdc_path, output, gdc_transport_parallel,
                                          gdc_udt)
        cli.check_code('Gdc', return_code)


def status_tables(repos, fileids, manifest, api_url, no_files):
    logger = logging.getLogger('__log__')
    repo_list = []
    gdc_ids = []
    cghub_ids = []
    repo_sizes = {}
    repo_counts = {}
    repo_donors = {}
    donors = []
    type_donors = {}
    type_sizes = {}
    type_counts = {}
    total_size = 0

    file_table = [["", "Size", "Unit", "File Format", "Data Type", "Repo"]]
    summary_table = [["", "Size", "Unit", "File Count", "Donor_Count"]]
    if manifest:
        if len(fileids) > 1:
            logger.warning("For download from manifest files, multiple manifest id arguments is not supported")
            raise click.BadArgumentUsage("Multiple manifest files specified.")

        portal = portal_client.IcgcPortalClient()
        manifest_json = cli.api_error_catch(portal.get_manifest_id, fileids[0], api_url, repos)

        fileids = cli.filter_manifest_ids(manifest_json)

    if not repos:
        raise click.BadOptionUsage("Must include prioritized repositories")
    for repository in repos:
        repo_sizes[repository] = OrderedDict({"total": 0})
        repo_counts[repository] = {"total": 0}
        repo_donors[repository] = {"total": []}
    portal = portal_client.IcgcPortalClient()
    entities = portal.get_metadata_bulk(fileids, api_url)
    count = len(entities)
    for entity in entities:
        size = entity["fileCopies"][0]["fileSize"]
        total_size += size
        repository, copy = cli.match_repositories(repos, entity)
        data_type = entity["dataCategorization"]["dataType"]
        if data_type not in type_donors:
            type_donors[data_type] = []
            type_counts[data_type] = 0
            type_sizes[data_type] = 0
        if data_type not in repo_donors[repository]:
            repo_donors[repository][data_type] = []
        filesize = file_size(size)
        if not no_files:
            file_table.append([entity["id"], filesize[0], filesize[1], copy["fileFormat"],
                               entity["dataCategorization"]["dataType"], repository])
        if repository == "gdc":
            gdc_ids.append(entity["dataBundle"]["dataBundleId"])
        if repository == "cghub":
            cghub_ids.append(entity["dataBundle"]["dataBundleId"])
        for donor_info in entity['donors']:
            repo_donors[repository]["total"] = donor_addition(repo_donors[repository]["total"], donor_info)
            repo_donors[repository][data_type] = donor_addition(repo_donors[repository][data_type], donor_info)
            donors = donor_addition(donors, donor_info)
            type_donors[data_type] = donor_addition(type_donors[data_type], donor_info)

        type_sizes[data_type] += size
        repo_sizes, repo_counts = increment_types(data_type, repository, repo_sizes, repo_counts, size)
        type_counts[data_type] += 1

    for repo in repo_sizes:
        for data_type in repo_sizes[repo]:
            filesize = file_size(repo_sizes[repo][data_type])
            name = repo + ": " + data_type
            summary_table.append([name, filesize[0], filesize[1], repo_counts[repo][data_type],
                                  len(repo_donors[repo][data_type])])
            repo_list.append(repo)

    filesize = file_size(total_size)
    summary_table.append(["Total", filesize[0], filesize[1], count, len(donors)])
    for data_type in type_sizes:
        filesize = file_size(type_sizes[data_type])
        summary_table.append([data_type, filesize[0], filesize[1], type_counts[data_type], len(type_donors[data_type])])
    if not no_files:
        logger.info(tabulate(file_table, headers="firstrow", tablefmt="fancy_grid", numalign="right"))
    logger.info(tabulate(summary_table, headers="firstrow", tablefmt="fancy_grid", numalign="right"))
    return gdc_ids, cghub_ids, repo_list


def access_checks(repo_list, cghub_access, cghub_path, ega_access, gdc_access, icgc_access, output, api_url,
                  gdc_ids=None, cghub_ids=None):
    logger = logging.getLogger('__log__')
    if "collaboratory" in repo_list:
        cli.check_access(icgc_access, "icgc")
        icgc_client = StorageClient()
        cli.access_response(icgc_client.access_check(icgc_access, repo="collab", api_url=api_url), "Collaboratory.")
    if "aws-virginia" in repo_list:
        cli.check_access(icgc_access, "icgc")
        icgc_client = StorageClient()
        cli.access_response(icgc_client.access_check(icgc_access, repo="aws", api_url=api_url), "Amazon Web server.")
    if 'ega' in repo_list:
        cli.check_access(ega_access, 'ega')
        ega_client = EgaDownloadClient()
        cli.access_response(ega_client.access_check(ega_access), "ega.")
    if 'gdc' in repo_list and gdc_ids:  # We don't get general access credentials to gdc, can't check without files.
        cli.check_access(gdc_access, 'gdc')
        gdc_client = GdcDownloadClient()
        gdc_result = cli.api_error_catch(gdc_client.access_check, gdc_access, gdc_ids)
        cli.access_response(gdc_result, "gdc files specified.")
    if 'cghub' in repo_list and cghub_ids:  # as before, can't check cghub permissions without files
        cli.check_access(cghub_access, 'cghub')
        gt_client = GnosDownloadClient()
        try:
            cli.access_response(gt_client.access_check(cghub_access, cghub_ids, cghub_path, output=output),
                                "cghub files.")
        except SubprocessError as e:
            logger.error(e.message)
            raise click.Abort
