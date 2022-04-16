# -*- coding: utf-8 -*-

from odoo import models, api
from collections import defaultdict


class LocalImportReportXls(models.AbstractModel):
    _name = 'report.local_import.local_import_report_xls'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, landed_cost):
        merge_format = workbook.add_format({
            'bold': 1,
            'border': 0,
            'align': 'left',
            'valign': 'vcenter'
        })
        merge_format.set_font_size(9)

        end_col = 0.0
        for obj in landed_cost:
            report_name = obj.name
            sheet = workbook.add_worksheet(report_name[:31])
            bold = workbook.add_format({'bold': True})
            sheet.merge_range('E1:I1', 'FONDO UTILIDADES TOTAL', merge_format)
            sheet.write(0, 4, 'Reporte   General de Costos de Liquidación', merge_format)
            sheet.write(3, 0, 'Lote:', merge_format)
            sheet.merge_range('A5:B5', 'Transporte:', merge_format)
            sheet.merge_range('A6:B6', 'Puerto de Embarque:', merge_format)
            sheet.merge_range('A7:B7', 'Puerto de Destino:', merge_format)
            sheet.write(7, 0, 'Fecha:', merge_format)

            sheet.write('C4', obj.freight_operation_id.name)
            sheet.write('C5', obj.freight_operation_id.transport)
            sheet.write('C6', obj.freight_operation_id.source_location_id.name)
            sheet.write('C7', obj.freight_operation_id.destination_location_id.name)
            date_format = workbook.add_format({'num_format': 'dd/mm/yy', 'align': 'left', })
            date_format.set_font_size(9)
            sheet.write('C8', obj.freight_operation_id.datetime, date_format)

            if obj.valuation_adjustment_lines:
                sheet.write(9, 0, 'PRODUCTO', merge_format)
                sheet.write(9, 1, 'PESO', merge_format)
                sheet.write(9, 2, 'VOLUMEN', merge_format)
                sheet.write(9, 3, 'CANTIDAD', merge_format)
                sheet.write(9, 4, 'UNIDAD DE MEDIDA', merge_format)
                sheet.write(9, 5, 'COSTO ANTERIOR (POR UNIDAD)', merge_format)
                sheet.write(9, 6, 'COSTO ANTERIOR', merge_format)

                temp_dict = self.create_dict_data(obj.valuation_adjustment_lines)

                for row, product_key in enumerate(temp_dict.keys(), 10):
                    sheet.write(row, 0, product_key)
                    for col, v in enumerate(temp_dict[product_key], 7):
                        sheet.write(row, 1, v.weight)
                        sheet.write(row, 2, v.volume)
                        sheet.write(row, 3, v.quantity)
                        sheet.write(row, 4, v.product_id.weight_uom_name)
                        sheet.write(row, 5, v.former_cost)
                        sheet.write(row, 6, v.final_cost)
                        sheet.write(9, col, v.cost_line_id.name.upper(), merge_format)
                        sheet.write(row, col, v.additional_landed_cost)
                        sheet.write(row, col + 1,
                                    v.former_cost + v.final_cost + self.calc_total_landed_cost(temp_dict, product_key))
                end_col = col + 1
                sheet.write(9, end_col, 'COSTO FINAL DEL PRODUCTO(POR UNIDAD)', merge_format)

    def create_dict_data(self, landed_cost_list):
        list_data = []

        for line in landed_cost_list:
            list_data.append((line.product_id.name, line))
        dict_data = defaultdict(list)

        for new_k, new_val in list_data:
            dict_data[new_k].append(new_val)

        return dict_data

    def calc_total_landed_cost(self, temp_dict, product_key):
        total_cost = 0.0
        for value in temp_dict[product_key]:
            total_cost = total_cost + value.additional_landed_cost
        return total_cost
