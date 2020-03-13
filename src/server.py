import os
import time

from flask import Flask, Response
from io import BytesIO, StringIO
from tarfile import TarFile, TarInfo


app = Flask(__name__)


class TarFileBuffer(object):
    def __init__(self):
        self._buffer = BytesIO()

    def write(self, data):
        self._buffer.write(data)

    def get_value(self):
        return self._buffer.getvalue()

    def reset(self):
        self._buffer.close()
        self._buffer = BytesIO()


def get_artifact_file_path(artifact_file_name):
    directory_path = os.path.abspath(os.getcwd())
    return os.path.join(
        directory_path,
        'src/log_files/',
        artifact_file_name
    )


def get_file_size(file: StringIO):
    pos = file.tell()
    file.seek(0, os.SEEK_END)
    length = file.tell()
    file.seek(pos)
    return length


def get_artifact_file(artifact_file_name: str):
    artifact_file_path = get_artifact_file_path(artifact_file_name)
    artifact_file = open(artifact_file_path, mode='r+b')
    artifact_file_info = TarInfo(artifact_file_name)
    artifact_file_info.size = get_file_size(artifact_file)
    return artifact_file_info, artifact_file


def streamed_tar_response():
    tar_file_buffer = TarFileBuffer()
    artifacts_tar = TarFile.open(
        name='artifacts.tar',
        mode='w:gz',
        fileobj=tar_file_buffer,
        dereference=True,
    )

    artifact_file_names = [
        'file_1.txt',
        'file_2.txt',
    ]

    for artifact_file_name in artifact_file_names:
        artifact_file_info, artifact_file = get_artifact_file(artifact_file_name)
        artifacts_tar.addfile(artifact_file_info, artifact_file)
        yield tar_file_buffer.get_value()
        tar_file_buffer.reset()
        time.sleep(5)

    artifacts_tar.close()
    yield tar_file_buffer.get_value()


@app.route('/')
def hello_world():
    return 'Hello World'


@app.route('/download')
def download_all_artifacts():
    response = Response(streamed_tar_response(), mimetype="application/x-tar")
    response.headers['Content-Disposition'] = 'attachment; filename=artifacts.tar'
    return response
