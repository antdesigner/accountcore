# -*- coding: utf-8 -*-
import json
import operator
import re
from odoo import http, exceptions
from odoo.http import serialize_exception, request
from odoo.addons.web.controllers.main import ExcelExport, ExportXlsxWriter, content_disposition


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
