var voucherNumbers = $("td[tastics]");
var default_tastics = $("#default_tastics").text();
var tastics_select = $("#tastics_select")
$(function () {
    flashVouchersNumber(default_tastics);
    initTasticSelect();
});

function getVoucherNumber(str, voucher_number_tastics_id) {
    //获得在某一编号策略下的凭证编号
    var number = JSON.parse(str)[voucher_number_tastics_id];
    return number;
};

function flashVouchersNumber(voucher_number_tastics_id) {
    //刷新凭证编号
    $.each(voucherNumbers, function (i, n) {
        $(this).find(".number").text(getVoucherNumber($(this).attr("tastics"), voucher_number_tastics_id));
    });
};

function initTasticSelect() {
    tastics_select.on('change', function (e) {
        flashVouchersNumber($(e.target).find("option:selected").val());
    });

};