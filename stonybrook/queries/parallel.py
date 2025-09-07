from tqdm.contrib.concurrent import thread_map


def process_file(file):
    # upload or compress or parse
    return some_result


results = thread_map(process_file, list_of_files, max_workers=10)
