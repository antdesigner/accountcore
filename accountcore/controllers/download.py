# -*- coding: utf-8 -*-
import datetime
import io
import json
import operator
import re

from odoo import http, exceptions
from odoo.tools import pycompat
from odoo.tools.misc import xlwt
from odoo.tools.translate import _
from odoo.exceptions import UserError
from odoo.http import serialize_exception, request
from odoo.addons.web.controllers.main import ExportFormat, content_disposition

# 导出EXCLE的基类


class ExcelExportBase(ExportFormat, http.Controller):
    # Excel needs raw data to correctly handle numbers and date values
    raw_data = True
    widths = {}
    default_widths = 8000

    def index_base(self, data, token, listType):
        self.listType = listType
        params = json.loads(data)
        model, fields, ids, domain = \
            operator.itemgetter('model', 'fields', 'ids',
                                'domain')(params)
        # 表头
        columns_headers = self.listType.get_colums_headers(fields)
        self.column_count = len(columns_headers)
        Model = request.env[model].sudo().with_context(
            **params.get('context', {}))
        Model = request.env[model].with_context(**params.get('context', {}))
        records = Model.browse(ids) or Model.search(
            domain, offset=0, limit=False, order=False)
        self.row_count = len(records)
        # 表体
        export_data = self.listType.get_export_data(records)
        response_data = self.from_data(columns_headers, export_data)
        return request.make_response(response_data,
                                     headers=[('Content-Disposition',
                                               content_disposition(self.filename(Model._description))),
                                              ('Content-Type', self.content_type)],
                                     cookies={'fileToken': token})

    @property
    def content_type(self):
        return 'application/vnd.ms-excel'

    def filename(self, base):
        return base + '.xls'

    def from_data(self, fields, rows):
        if len(rows) > 65535:
            raise UserError(
                _('导出的行数过多 (%s 行, 上限为: 65535行) , 请分多次导出') % len(rows))

        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet('Sheet 1')
        header_style = xlwt.easyxf(
            'font:bold True;align: vert center, horiz center;')
        for i, fieldname in enumerate(fields):
            worksheet.write(0, i, fieldname, header_style)
            worksheet.col(i).width = self.setColumnWidth(
                worksheet.col(i), fieldname)  # around 220 pixels

        base_style = xlwt.easyxf('align: wrap yes')
        date_style = xlwt.easyxf(
            'align: wrap yes', num_format_str='YYYY-MM-DD')
        datetime_style = xlwt.easyxf(
            'align: wrap yes', num_format_str='YYYY-MM-DD HH:mm:SS')

        for row_index, row in enumerate(rows):
            for cell_index, cell_value in enumerate(row):
                cell_style = base_style
                if isinstance(cell_value, bytes) and not isinstance(cell_value, pycompat.string_types):
                    try:
                        cell_value = pycompat.to_text(cell_value)
                    except UnicodeDecodeError:
                        raise UserError(
                            _("Binary fields can not be exported to Excel unless their content is base64-encoded. That does not seem to be the case for %s.") % fields[cell_index])

                if isinstance(cell_value, pycompat.string_types):
                    cell_value = re.sub(
                        "\r", " ", pycompat.to_text(cell_value))
                    # Excel supports a maximum of 32767 characters in each cell:
                    cell_value = cell_value[:32767]
                elif isinstance(cell_value, datetime.datetime):
                    cell_style = datetime_style
                elif isinstance(cell_value, datetime.date):
                    cell_style = date_style
                worksheet.write(row_index + 1, cell_index,
                                cell_value, cell_style)

        fp = io.BytesIO()
        workbook.save(fp)
        fp.seek(0)
        data = fp.read()
        fp.close()
        return data

    def setColumnWidth(self, column, fieldname):
        return self.listType.widths.get(fieldname, ExcelExportBase.default_widths)

    @http.route('/web/export/accountcore.voucher', type='http', auth="user")
    # @serialize_exception
    def accountcore_voucher(self, data, token):
        listType = ExcelExportVouchers()
        return self.index_base(data, token, listType)

    @http.route('/web/export/accountcore.entry', type='http', auth="user")
    # @serialize_exception
    def accountcore_entry(self, data, token):
        listType = ExcelExportEntrys()
        return self.index_base(data, token, listType)

    @http.route('/web/export/accountcore.account', type='http', auth="user")
    # @serialize_exception
    def accountcore_account(self, data, token):
        listType = ExcelExportAccounts()
        return self.index_base(data, token, listType)

    @http.route('/web/export/accountcore.item', type='http', auth="user")
    # @serialize_exception
    def accountcore_item(self, data, token):
        listType = ExcelExportItems()
        return self.index_base(data, token, listType)

    @http.route('/web/export/accountcore.org', type='http', auth="user")
    # @serialize_exception
    def accountcore_org(self, data, token):
        listType = ExcelExportOrgs()
        return self.index_base(data, token, listType)

# 凭证列表导出EXCEL


class ExcelExportVouchers():
    # 列宽
    widths = {"记账日期": 4000,
              "凭证号": 1800,
              "分录摘要": 10000,
              "科目编码": 3000,
              "会计科目": 10000,
              "核算统计项目": 15000,
              "借方金额": 3000,
              "贷方金额": 3000,
              "现金流量": 15000,
              "唯一编号": 2500,
              "核算机构": 8000,
              "凭证的标签": 4000,
              "审核人": 3000,
              "全局标签": 4000,
              "策略号": 1800,
              "制单人": 3000,
              "附件张数": 2000,
              "凭证来源": 2000}

    def get_colums_headers(self, fields):
        field_names = [f['name'] for f in fields]
        entry_index = field_names.index('entrysHtml')
        columns_headers = [val['label'].strip() for val in fields]
        columns_headers_befor_entry = columns_headers[0:entry_index]
        columns_headers_after_entry = columns_headers[entry_index+1:]
        columns_headers = columns_headers_befor_entry + \
            ['分录说明', '科目编码', '会计科目', '核算统计项目', '借方金额',
                '贷方金额', '现金流量']+columns_headers_after_entry
        return columns_headers

    def get_export_data(self, records):
        export_data = []
        vouchers = records
        for v in vouchers:
            glob_tags = [g.name for g in v.glob_tag]
            glot_tags_str = '/'.join(glob_tags)
            voucher_before_entry = [v.voucherdate, v.v_number]
            v_after_entry = [v.uniqueNumber,
                             v.org.name,
                             re.sub(r'<br>|<p>|</p>', '', v.roolbook_html),
                             v.reviewer.name,
                             glot_tags_str,
                             v.number,
                             v.createUser.name,
                             v.appendixCount,
                             v.soucre.name]
            entrys = v.entrys
            for e in entrys:
                items = re.sub(r'<br>|<p>|</p>', '', e.items_html)
                entry = [e.explain, e.account.number, e.account.name,
                         items, e.damount, e.camount, e.cashFlow.name]
                entry_line = []
                entry_line.extend(voucher_before_entry)
                entry_line.extend(entry)
                entry_line.extend(v_after_entry)
                export_data.append(entry_line)
        return export_data


# 分录列表导出EXCEL


class ExcelExportEntrys():
    widths = {"记账日期": 3000,
              "凭证号": 1800,
              "分录摘要": 10000,
              "科目编码": 3000,
              "会计科目": 10000,
              "借方金额": 3000,
              "贷方金额": 3000,
              "核算统计项目": 15000,
              "现金流量": 15000,
              "所属凭证": 2500,
              "唯一编号": 2500,
              "核算机构": 8000,
              "业务日期": 4000,
              "全局标签": 4000}

    def get_colums_headers(self, fields):
        field_names = [f['name'] for f in fields]
        entry_index = field_names.index('account')
        columns_headers = [val['label'].strip() for val in fields]
        columns_headers_befor_entry = columns_headers[0:entry_index]
        columns_headers_after_entry = columns_headers[entry_index+1:]
        columns_headers = columns_headers_befor_entry + \
            ['科目编码', '会计科目']+columns_headers_after_entry
        return columns_headers

    def get_export_data(self, records):
        export_data = []
        entry = records
        for e in entry:
            glob_tags = [g.name for g in e.glob_tag]
            glot_tags_str = '/'.join(glob_tags)
            items = re.sub(r'<br>|<p>|</p>', '', e.items_html)
            entry_line = [e.v_voucherdate,
                          e.v_number,
                          e.explain,
                          e.account.number,
                          e.account.name,
                          items,
                          e.damount,
                          e.camount,
                          e.cashFlow.name,
                          e.voucher.name,
                          e.org.name,
                          e.v_real_date,
                          glot_tags_str]
            export_data.append(entry_line)
        return export_data

# 会计科目列表导出EXCEL


class ExcelExportAccounts():
    widths = {"所属机构": 8000,
              "所属科目体系": 3500,
              "科目类别": 2500,
              "科目编码": 3000,
              "科目名称": 10000,
              "核算类别": 6000,
              "余额方向": 2500,
              "凭证中可选": 3000,
              "末级科目": 2500,
              "全局标签": 8000}

    def get_colums_headers(self, fields):
        columns_headers = [val['label'].strip() for val in fields]
        return columns_headers

    def get_export_data(self, records):
        export_data = []
        lines = records
        for line in lines:
            glob_tags = [g.name for g in line.glob_tag]
            glob_tags_str = '/'.join(glob_tags)
            orgs = [o.name for o in line.org]
            orgs_str = '/'.join(orgs)
            direction = "借"
            if line.direction == "-1":
                direction = "贷"
            excel_line = [orgs_str,
                          line.accountsArch.name,
                          line.accountClass.name,
                          line.number,
                          line.name,
                          line.itemClassesHtml,
                          direction,
                          line.is_show,
                          line.is_last,
                          glob_tags_str]
            export_data.append(excel_line)
            export_data.sort(key=lambda e: e[3])
        return export_data

# 核算项目列表导出EXCEL


class ExcelExportItems():
    widths = {"所属机构": 8000,
              "核算项目类别": 4000,
              "核算项目编码": 4000,
              "核算项目名称": 12000,
              "唯一编号": 2500,
              "全局标签": 8000}

    def get_colums_headers(self, fields):
        columns_headers = [val['label'].strip() for val in fields]
        columns_headers = ["核算项目名称" if one ==
                           "Display Name" else one for one in columns_headers]
        return columns_headers

    def get_export_data(self, records):
        export_data = []
        lines = records
        for line in lines:
            glob_tags = [g.name for g in line.glob_tag]
            glob_tags_str = '/'.join(glob_tags)
            orgs = [o.name for o in line.org]
            orgs_str = '/'.join(orgs)
            excel_line = [orgs_str,
                          line.item_class_name,
                          line.number,
                          line.name,
                          line.uniqueNumber,
                          glob_tags_str]
            export_data.append(excel_line)
            export_data.sort(key=lambda e: e[1])
        return export_data

# 核算项目列表导出EXCEL


class ExcelExportOrgs():
    widths = {"核算机构编码": 5000,
              "核算机构名称": 12000,
              "全局标签": 12000}

    def get_colums_headers(self, fields):
        columns_headers = [val['label'].strip() for val in fields]
        columns_headers.remove("当前机构")
        return columns_headers

    def get_export_data(self, records):
        export_data = []
        lines = records
        for line in lines:
            glob_tags = [g.name for g in line.glob_tag]
            glob_tags_str = '/'.join(glob_tags)
            excel_line = [line.number,
                          line.name,
                          glob_tags_str]
            export_data.append(excel_line)
        return export_data
