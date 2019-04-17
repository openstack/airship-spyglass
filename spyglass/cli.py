# Copyright 2019 AT&T Intellectual Property.  All other rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import pprint

import click
from click_plugins import with_plugins
import pkg_resources
import yaml

from spyglass.parser.engine import ProcessDataSource
from spyglass.site_processors.site_processor import SiteProcessor

LOG = logging.getLogger(__name__)

LOG_FORMAT = '%(asctime)s %(levelname)-8s %(name)s:' \
             '%(funcName)s [%(lineno)3d] %(message)s'

CONTEXT_SETTINGS = {
    'help_option_names': ['-h', '--help'],
}

TEMPLATE_DIR_OPTION = click.option(
    '-t',
    '--template-dir',
    'template_dir',
    type=click.Path(exists=True, readable=True, file_okay=False),
    required=True,
    help='Path to the directory containing manifest J2 templates.')

MANIFEST_DIR_OPTION = click.option(
    '-m',
    '--manifest-dir',
    'manifest_dir',
    type=click.Path(exists=True, writable=True, file_okay=False),
    required=False,
    help='Path to place created manifest files.')


@click.option(
    '-v',
    '--verbose',
    is_flag=True,
    default=False,
    help='Enable debug messages in log.')
@with_plugins(pkg_resources.iter_entry_points('cli_plugins'))
@click.group()
def main(*, verbose):
    """CLI for Airship Spyglass"""
    if verbose:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO
    logging.basicConfig(format=LOG_FORMAT, level=log_level)


def intermediary_processor(plugin_type, **kwargs):
    LOG.info("Generating Intermediary yaml")
    plugin_type = plugin_type
    plugin_class = None

    # Discover the plugin and load the plugin class
    LOG.info("Load the plugin class")
    for entry_point in \
            pkg_resources.iter_entry_points('data_extractor_plugins'):
        LOG.debug("Entry point '%s' found", entry_point.name)
        if entry_point.name == plugin_type:
            plugin_class = entry_point.load()

    if plugin_class is None:
        LOG.error(
            "Unsupported Plugin type. Plugin type:{}".format(plugin_type))
        exit()

    # Extract data from plugin data source
    LOG.info("Extract data from plugin data source")
    data_extractor = plugin_class(kwargs['site_name'])
    plugin_conf = data_extractor.get_plugin_conf(**kwargs)
    data_extractor.set_config_opts(plugin_conf)
    data_extractor.extract_data()

    # Apply any additional_config provided by user
    additional_config = kwargs.get('site_configuration', None)
    if additional_config is not None:
        with open(additional_config, 'r') as config:
            raw_data = config.read()
            additional_config_data = yaml.safe_load(raw_data)
        LOG.debug(
            "Additional config data:\n{}".format(
                pprint.pformat(additional_config_data)))

        LOG.info(
            "Apply additional configuration from:{}".format(additional_config))
        data_extractor.apply_additional_data(additional_config_data)
        LOG.debug(pprint.pformat(data_extractor.site_data))

    # Apply design rules to the data
    LOG.info("Apply design rules to the extracted data")
    process_input_ob = ProcessDataSource(kwargs['site_name'])
    process_input_ob.load_extracted_data_from_data_source(
        data_extractor.site_data)
    return process_input_ob


@main.command(
    'mi',
    short_help='generates manifest from intermediary',
    help='Generate manifest files from specified intermediary file.')
@click.argument(
    'intermediary_file',
    type=click.Path(exists=True, readable=True, dir_okay=False))
@TEMPLATE_DIR_OPTION
@MANIFEST_DIR_OPTION
def generate_manifests_using_intermediary(
        *, intermediary_file, template_dir, manifest_dir):
    LOG.info("Loading intermediary from user provided input")
    with open(intermediary_file, 'r') as f:
        raw_data = f.read()
        intermediary_yaml = yaml.safe_load(raw_data)

    LOG.info("Generating site Manifests")
    processor_engine = SiteProcessor(intermediary_yaml, manifest_dir)
    processor_engine.render_template(template_dir)
