"""
Parse dbt models into 
"""
import logging
import os
import pathlib
import markdown

import yaml

# set up logging to file
HTML_OUTPUT_TYPE = "HTML"
MARKDOWN_OUTPUT_TYPE = "MARKDOWN"

logging.basicConfig(
    filename='log_file_name.log',
    level=logging.INFO,
    format='[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)

# set up logging to console
console = logging.StreamHandler()
console.setLevel(logging.DEBUG)
# set a format which is simpler for console use
formatter = logging.Formatter('[%(asctime)s]: %(name)-12s: %(levelname)-8s %(message)s')
console.setFormatter(formatter)
# add the handler to the root logger
logging.getLogger('').addHandler(console)

logger = logging.getLogger(__name__)



def html_file_path(file_name, target_path):
    """
    get file path for html file
    :param file_name:
    :param target_path:
    :return:
    """
    extention = ".html"
    file = file_name + extention  # create new file name for markdown
    # save markdown file
    file_path = os.path.join(target_path, file)
    return file_path


def export_to_html(html_path, yaml_file):
    """
    save documentation as html
    :param html_path: path to save file
    :param yaml_file: path to yaml file
    :return: number of lines saved to markdown file
    """
    lines = get_model_names(yaml_file)  # convert yaml to lines of markdown file
    content = "\n".join(lines)  # turn lines into a single multiline string
    number_of_lines = save_file(content, html_path)
    logging.debug(f"{html_path}: {number_of_lines}")
    return number_of_lines



def parse_models(models_path, output_path=None, generate_html=False):
    """
    Traverse a path of dbt models and process yaml files
    :param models_path:
    :return:
    """
    logging.info('Starting up')
    logging.info(f'models path: {models_path}')

    line_count = dict()

    starting_path_parts = models_path.split(os.path.sep)
    output_path_parts = output_path.split(os.path.sep)

    header_lines = ["<HTML>", "<HEAD></HEAD>", "<BODY>", "Links to models", "<table> <thead> <tr> <th>Retailer</th> <th>Models</th> </tr> </thead> <tbody>" ]
    index_lines = []
    # traverse root directory, and list directories as dirs and files as files
    for root, dirs, files in os.walk(models_path):
        # path = root.split(os.path.sep)

        logging.info(root)
        path = root.split(os.path.sep)
        logging.info(path)

        # remove starting path from current path and replace with output path
        p = trim_base_path(path, starting_path_parts)
        subdirectory = os.path.sep.join(p)
        o = list(output_path_parts)
        o.extend(p)  # add whatever parts are remaining to output path
        # print(o)
        target_path = os.path.sep.join(o)
        pathlib.Path(target_path).mkdir(parents=True, exist_ok=True)

        logging.info(f"output path: {o}")

        for file in files:
            if is_yaml(file):

                yaml_file = os.path.join(root, file)  # combine directory and file name
                logging.info(f"yaml file: {yaml_file}")

                file_name = file_name_without_extension(file)  # get file name without extension
                markdown_path = markdown_file_path(file_name, target_path)
                lines = process_yaml(yaml_file)  # convert yaml to lines of markdown file
                markdown_doc = "\n".join(lines)  # turn lines into a single multiline string
                of_lines = save_file(markdown_doc, markdown_path)
                logging.debug(f"{markdown_path}: {of_lines}")
                number_of_lines = of_lines

                line_count[markdown_path] = number_of_lines

                if generate_html:

                    html_doc = markdown.markdown(markdown_doc, extensions=['tables'])
                    html_path = html_file_path(file_name,target_path)
                    save_file(html_doc, html_path)

                    models = get_model_names(yaml_file)
                    logging.info(f"target_path: {target_path}")

                    extention = ".html"
                    file = file_name + extention  # create new file name for markdown
                    html_sub_path = os.path.join(subdirectory,file)
                    parent_dir = parent_directory(html_path)
                    if len(models)>0:
                        index_lines.append(f"<tr> <td>{parent_dir}</td> <td><a href='{html_sub_path}'>{','.join(models)}</td> </tr>")

    footer_lines = [" </tbody> </table>","</BODY></HTML>"]
    index_file_path = os.path.join(output_path,"index.html")
    i_lines = header_lines+sorted(index_lines)+footer_lines # combine header, table lines and footer
    save_file("\n".join(i_lines),index_file_path)




    return line_count


def trim_base_path(path, starting_path_parts):
    """
    remove early parts of path assuming two paths overlap
    :param path: longer path
    :param starting_path_parts: beginning part of path to remove
    :return: ending part of the longer path
    """
    s = list(starting_path_parts)
    p = list(path)
    for i in s:  # for each part in the starting path
        p.pop(0)  # remove a part of path (starting from the left)
    return p


def save_file(contents, save_path):
    n = None
    with open(save_path, "w") as f:
        n = f.write(contents)
    logging.debug(f"lines written {save_path}: {n}")
    number_of_lines = n  # save markdown file
    return number_of_lines


def file_name_without_extension(file):
    """
    get file name without extension
    :param file: file name with extension
    :return: file name without extension
    """
    split_tup = os.path.splitext(file)  # get filename without extension
    # extract the file name and extension
    file_name = split_tup[0]
    return file_name


def markdown_file_path(file_name, target_path):
    markdown_extension = ".md"
    markdown_file = file_name + markdown_extension  # create new file name for markdown
    # save markdown file
    markdown_path = os.path.join(target_path, markdown_file)
    return markdown_path


def yaml_to_dict(file_path):
    """
    parse yaml to dictionary from file path
    :param file_path: path to yaml file
    :return:
    """
    yaml_obj = None
    with open(file_path, 'r') as file:
        yaml_obj = yaml.safe_load(file)

    return yaml_obj


def get_model_names(file_path):
    """
    get model names
    :param file_path: yaml file path
    :return: list of model names from yaml
    """
    names = []
    d = yaml_to_dict(file_path)  # parse yaml
    models = d.get("models")

    if models:
        for item in models:  # get markdown for each model
            name = item.get("name")
            names.append(name)
    return names

def parent_directory(file_path):
    path_parts = file_path.split(os.path.sep)
    return path_parts[-2]


def process_yaml(file_path):
    """
    process yaml file
    :param file_path: path to file
    :return: lines of markdown file with dbt model info
    """
    logging.info(f"processing YAML file {file_path}")

    lines = []

    parent_dir=parent_directory(file_path)
    lines.append(format_title(os.path.basename(file_path) + " - " + parent_dir))  # add title

    d = yaml_to_dict(file_path)  # parse yaml
    models = []
    for key in d:
        if key == "version":
            lines.append(format_version(d["version"]))  # add version
        if key == "models":
            models = d["models"]  # parse out model dictionary for processing

    for item in models:  # get markdown for each model
        model_md = model_to_markdown(item)
        lines.extend(model_md)  # add to the lines of markdown

    return lines


def model_to_markdown(item):
    """
    process dbt model into markdown
    :param item: dictionary object with model
    :return: list of markdown strings
    """
    lines = []
    for key in item:
        # print(f"{key}:{item[key]}")
        if key == "name":
            lines.append(format_name(item["name"]))
        meta = None
        if key == "meta":
            meta = item[key]
            for mkey in meta:
                if key == "owner":
                    lines.append(format_owner(meta[mkey]))
        if key == "description":
            lines.append(format_description(item["description"]))
        if key == "columns":
            lines.append(format_column_header())
            for column in item["columns"]:
                name = column.get("name")
                desc = column.get("description")
                # print(f"{ckey}:{column[ckey]}")
                lines.append(format_column(name, desc))
            lines.append("\n")

    return lines


def format_name(s):
    return f"## {s} \n"


def format_description(s):
    return f"{s}\n"


def format_column_header():
    lines = []
    lines.append(f"| Name | Description |")
    lines.append(f"| ---- | ----------- | ")
    return "\n".join(lines)


def format_column(name, description):
    return f"| {name} | {description} |"


def format_owner(s):
    return f"### Owner: {s} \n"


def format_version(s):
    return f"#### Version: {s} \n"


def format_title(input_string):
    return f"# {input_string} \n"


def is_yaml(filename):
    """
    parse filename to check if it's yaml file
    :param filename: path to file
    :return: True if extension is yml
    """
    logging.debug(f"processing {filename}")
    # this will return a tuple of root and extension
    split_tup = os.path.splitext(filename)
    # extract the file name and extension
    file_name = split_tup[0]
    file_extension = split_tup[1]

    if file_extension.lower() == ".yml":
        return True

    return False


class Formatter():
    def __init__(self, file_path):
        self.file_path = file_path
        self.content = yaml_to_dict(file_path)

    def title(self):
        return os.path.basename(self.file_path)

    def models(self):
        """
        get markdown for models in file
        :return:
        """
        d = self.content
        models = []
        for key in d:
            if key == "models":
                for item in d["models"]:
                    models.append(self.model(item))

    def model(self, item):
        for key in item:
            pass


if __name__ == "__main__":
    n = parse_models("./tests/models/base/business_vault", "./output/business_vault", generate_html=True)
    # print(f"line count: {n}")
