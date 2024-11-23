import json
import os
import fitz
import pandas as pd
import matplotlib.pyplot as plt
import re
from matplotlib.ticker import FuncFormatter
import numpy as np
import matplotlib as mpl

mpl.use("pgf")
mpl.rcParams.update({
    "text.usetex":
        True,  # use default xelatex
    "pgf.texsystem":
        "xelatex",
    "font.family":
        "sans-serif",
    "font.sans-serif":
        "Times New Roman",
    "pgf.preamble":
        '\n'.join([
            "\\usepackage{xeCJK}",  # load CJK package
            "\\usepackage{metalogo}",
            "\\usepackage{unicode-math}",  # unicode math setup
            "\\usepackage{fontspec}",
            r"\setmainfont{Times New Roman}",
            r"\setCJKmainfont{SimSun}",  # serif font via preamble
        ])
})


def remove_comments_and_trailing_commas(json_string):
  """
    移除JSON字符串中的注释和多余的逗号。
    :param json_string: 包含注释和多余逗号的原始JSON字符串
    :return: 清理后的JSON字符串
    """
  # 移除单行注释
  json_string = re.sub(r'//.*', '', json_string)
  # 移除多行注释
  json_string = re.sub(r'/\*.*?\*/', '', json_string, flags=re.DOTALL)
  # 移除多余的逗号
  json_string = re.sub(r',(\s*[}\]])', r'\1', json_string)
  return json_string


def load_json_config(file_path):
  with open(file_path, 'r', encoding='utf8') as f:
    json_with_comments = f.read()

  cleaned_json_string = remove_comments_and_trailing_commas(json_with_comments)
  return json.loads(cleaned_json_string)


def detect_delimiter(text):
  """
    尝试检测剪切板内容的分隔符。
    :param text: 剪切板内容字符串
    :return: 检测到的分隔符
    """
  delimiters = ['\t', ',', ' ']
  for delimiter in delimiters:
    if re.search(f'{delimiter}', text):
      return delimiter
  return ','  # 默认返回逗号


def parse_data(config):
  data_file = config['data_file']
  if data_file.endswith('.csv'):
    df = pd.read_csv(data_file)
  elif data_file.endswith('.xlsx'):
    df = pd.read_excel(data_file)
  elif data_file == 'clipboard':
    import pyperclip
    clipboard_text = pyperclip.paste().strip()
    delimiter = detect_delimiter(clipboard_text)
    df = pd.read_clipboard(sep=delimiter)

  x_axis = config['x_axis']
  y_axis = config['y_axis']
  data_columns = config['data_columns']

  #获取实际列数
  ncol = df.shape[1]
  icol = 0
  for i in data_columns['x_column_indices']:
    if i < ncol:
      icol += 1
    else:
      break
  jcol = 0
  for i in data_columns['y_column_indices']:
    if i < ncol:
      jcol += 1
    else:
      break
  ncol = min(icol, jcol)
  
  if data_columns['lables'] == 'auto':
    lables = [df.columns[i] for i in data_columns['y_column_indices'][:ncol]]
  else:
    lables = data_columns['lables'][:ncol]

  x_data = [df.iloc[:, i] for i in data_columns['x_column_indices'][:ncol]]
  y_data = [df.iloc[:, i] for i in data_columns['y_column_indices'][:ncol]]

  return x_data, y_data, x_axis, y_axis, lables


def plot_graph(x_data, y_data, labels, x_axis, y_axis, config):
  plt.rcParams['text.usetex'] = True
  plt.rcParams['font.family'] = ['Times New Roman', 'SimSun']
  plt.rcParams['pgf.texsystem'] = 'xelatex'

  #plt.rcParams['text.latex.preamble']=r'\makeatletter \newcommand*{\rom}[1]{\expandafter\@slowromancap\romannumeral #1@} \makeatother'

  plt.rcParams['mathtext.fontset'] = 'stix'  # 使用 Stix 字体集以确保数学字体一致
  plt.rcParams['font.size'] = config['font_size']
  size = np.array(config['fig_size']) / 2.54
  fig, ax = plt.subplots(figsize=(size[0], size[1]))

  # 设置线条样式
  colors = config['data_styles']['colors']
  linestyles = config['data_styles']['linestyles']
  linewidths = config['data_styles']['linewidths']
  markers = config['data_styles']['markers']
  markersizes = config['data_styles']['markersizes']
  markerfacecolor = config['data_styles']['markerfacecolor']
  markeredgewidth = config['data_styles']['markeredgewidth']

  for i, (x, y) in enumerate(zip(x_data, y_data)):
    ax.plot(x,
            y,
            color=colors[i % len(colors)],
            linestyle=linestyles[i % len(linestyles)],
            linewidth=linewidths[i % len(linewidths)],
            marker=markers[i % len(markers)],
            markersize=markersizes[i % len(markersizes)],
            markerfacecolor=markerfacecolor[i % len(markerfacecolor)],
            markeredgewidth=markeredgewidth[i % len(markeredgewidth)],
            label=labels[i])

  # 设置X轴
  ax.set_xlabel(x_axis['label'])
  if x_axis['lim'] != 'auto':
    ax.set_xlim(x_axis['lim'])
  if x_axis['start_tick'] != 'auto' and x_axis['step'] != 'auto':
    tick_start = x_axis['start_tick']
    tick_end = ax.get_xlim()[1]
    step = x_axis['step']
    ticks = np.arange(tick_start, tick_end + step * 0.5, step)
    ax.set_xticks(ticks)
  ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: x_axis['format'] % x))
  if 'pad' in x_axis:
    ax.tick_params(axis='x', pad=x_axis['pad'])  # 使用pad参数下移刻度标签
  if 'font_size' in x_axis:
    ax.tick_params(axis='x', labelsize=x_axis['font_size'])  # 使用pad参数下移刻度标签

  # 设置Y轴
  ax.set_ylabel(y_axis['label'])
  if y_axis['lim'] != 'auto':
    ax.set_ylim(y_axis['lim'])
  if y_axis['start_tick'] != 'auto' and y_axis['step'] != 'auto':
    tick_start = y_axis['start_tick']
    tick_end = ax.get_xlim()[1]
    step = y_axis['step']
    ticks = np.arange(tick_start, tick_end + step * 0.5, step)
    ax.set_yticks(ticks)
  ax.yaxis.set_major_formatter(FuncFormatter(lambda y, _: y_axis['format'] % y))
  if 'pad' in y_axis:
    ax.tick_params(axis='x', pad=y_axis['pad'])  # 使用pad参数下移刻度标签
  if 'font_size' in y_axis:
    ax.tick_params(axis='x', labelsize=y_axis['font_size'])  # 使用pad参数下移刻度标签

  # 设置主刻度线方向
  ax.tick_params(axis='both', direction='in')
  ax.tick_params(top=True, right=True, labeltop=False, labelright=False)

  # 添加图例
  j_legend = config['legend']
  if j_legend['visible']:
    legend_frame = j_legend['frame']
    fsize = config['font_size']
    if 'font_size' in j_legend:
      fsize = j_legend['font_size']
    if 'anchor' in j_legend:
      legend = ax.legend(loc=j_legend['loc'],
                         ncol=j_legend['ncol'],
                         bbox_to_anchor=tuple(j_legend['anchor']),
                         fontsize=fsize)
    else:
      legend = ax.legend(loc=j_legend['loc'],
                         ncol=j_legend['ncol'],
                         fontsize=fsize)
    frame = legend.get_frame()
    # 设置图例的框架样式
    frame.set_visible(legend_frame['visible'])
    if legend_frame['visible']:
      frame.set_alpha(legend_frame['framealpha'])
      frame.set_edgecolor(legend_frame['edgecolor'])
      frame.set_linewidth(legend_frame['linewidth'])
      frame.set_boxstyle(f"round,pad={legend_frame['rounded']}")

  plt.tight_layout(pad=0.5)
  return fig
  #plt.show()


def pdf_to_svg(pdf_path, svg_path):
  # 打开 PDF 文件
  pdf_document = fitz.open(pdf_path)

  # 遍历 PDF 的每一页
  for page_num in range(pdf_document.page_count):
    page = pdf_document.load_page(page_num)

    # 将页面转换为 SVG 格式
    svg_data = page.get_svg_image()

    # 保存 SVG 文件
    with open(svg_path, 'w', encoding='utf-8') as svg_file:
      svg_file.write(svg_data)
    break

  pdf_document.close()


def export_svg(fig, filename):
  pdf_name = filename.replace('.svg', '.pdf')
  fig.savefig(pdf_name, dpi=400)
  pdf_to_svg(pdf_name, filename)
  os.remove(pdf_name)
  plt.close(fig)
  print(f"SVG 文件已保存到: {filename}")


if __name__ == "__main__":
  config = load_json_config('plot_config.json')  # 请确保路径正确
  x_data, y_data, x_axis, y_axis, labels = parse_data(config)
  fig = plot_graph(x_data, y_data, labels, x_axis, y_axis, config)
  export_svg(fig, config['out_file'])
