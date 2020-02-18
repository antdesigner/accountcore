# -*- coding: utf-8 -*-
import datetime
import io
import json
import operator
import re

from odoo import http, exceptions
from odoo.tools import pycompat
from odoo.tools.misc import xlsxwriter
from odoo.exceptions import UserError
from odoo.http import serialize_exception, request
from odoo.addons.web.controllers.main import ExcelExport, content_disposition

class ExcelExportExport(ExcelExport):
    @http.route('/web/export/ac_xlsx', type='http', auth="user")
    # @serialize_exception
    def ac_index(self, data, token):
        params = json.loads(data)
        model, fields, ids, domain, import_compat = \
            operator.itemgetter('model', 'fields', 'ids',
                                'domain', 'import_compat')(params)

        field_names = [f['name'] for f in fields]
        entry_index = field_names.index('entrysHtml')
        if import_compat:
            columns_headers = field_names
        else:
            columns_headers = [val['label'].strip() for val in fields]
            columns_headers_befor_entry = columns_headers[0:entry_index]
            columns_headers_after_entry = columns_headers[entry_index+1:]
            columns_headers = columns_headers_befor_entry + \
                ['分录说明', '科目编码', '会计科目', '核算统计项目', '借方金额',
                    '贷方金额', '现金流量']+columns_headers_after_entry

        Model = request.env[model].sudo().with_context(
            **params.get('context', {}))
        # groupby = params.get('groupby')
        export_data = []
        vouchers = Model.search(domain)
        for v in vouchers:
            glob_tags = [g.name for g in v.glob_tag]
            glot_tags_str = '/'.join(glob_tags)
            voucher_before_entry = [v.voucherdate, v.v_number]
            v_after_entry = [v.uniqueNumber,
                             v.org.name,
                             v.roolbook_html,
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
        response_data = self.from_data(columns_headers, export_data)
        return request.make_response(response_data,
                                     headers=[('Content-Disposition',
                                               content_disposition(self.filename("凭证列表"))),
                                              ('Content-Type', self.content_type)],
                                     cookies={'fileToken': token})

    def from_data(self, fields, rows):
        with ExportXlsxWriter(fields, len(rows)) as xlsx_writer:
            for row_index, row in enumerate(rows):
                for cell_index, cell_value in enumerate(row):
                    xlsx_writer.write_cell(
                        row_index + 1, cell_index, cell_value)
        return xlsx_writer.value

class ExportXlsxWriter:
    '''从odoo13中复制过来'''
    def __init__(self, field_names, row_count=0):
        self.field_names = field_names
        self.output = io.BytesIO()
        self.workbook = xlsxwriter.Workbook(self.output, {'in_memory': True})
        self.base_style = self.workbook.add_format({'text_wrap': True})
        self.header_style = self.workbook.add_format({'bold': True})
        self.header_bold_style = self.workbook.add_format(
            {'text_wrap': True, 'bold': True, 'bg_color': '#e9ecef'})
        self.date_style = self.workbook.add_format(
            {'text_wrap': True, 'num_format': 'yyyy-mm-dd'})
        self.datetime_style = self.workbook.add_format(
            {'text_wrap': True, 'num_format': 'yyyy-mm-dd hh:mm:ss'})
        self.worksheet = self.workbook.add_worksheet()
        self.value = False

        if row_count > self.worksheet.xls_rowmax:
            raise UserError(_('There are too many rows (%s rows, limit: %s) to export as Excel 2007-2013 (.xlsx) format. Consider splitting the export.') %
                            (row_count, self.worksheet.xls_rowmax))

    def __enter__(self):
        self.write_header()
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.close()

    def write_header(self):
        # Write main header
        for i, fieldname in enumerate(self.field_names):
            self.write(0, i, fieldname, self.header_style)
        self.worksheet.set_column(0, i, 30)
        # around 220 pixels

    def close(self):
        self.workbook.close()
        with self.output:
            self.value = self.output.getvalue()

    def write(self, row, column, cell_value, style=None):
        self.worksheet.write(row, column, cell_value, style)

    def write_cell(self, row, column, cell_value):
        cell_style = self.base_style

        if isinstance(cell_value, bytes):
            try:
                # because xlsx uses raw export, we can get a bytes object
                # here. xlsxwriter does not support bytes values in Python 3 ->
                # assume this is base64 and decode to a string, if this
                # fails note that you can't export
                cell_value = pycompat.to_text(cell_value)
            except UnicodeDecodeError:
                raise UserError(
                    _("Binary fields can not be exported to Excel unless their content is base64-encoded. That does not seem to be the case for %s.") % self.field_names[column])

        if isinstance(cell_value, str):
            if len(cell_value) > self.worksheet.xls_strmax:
                cell_value = _(
                    "The content of this cell is too long for an XLSX file (more than %s characters). Please use the CSV format for this export.") % self.worksheet.xls_strmax
            else:
                cell_value = cell_value.replace("\r", " ")
        elif isinstance(cell_value, datetime.datetime):
            cell_style = self.datetime_style
        elif isinstance(cell_value, datetime.date):
            cell_style = self.date_style
        self.write(row, column, cell_value, cell_style)
