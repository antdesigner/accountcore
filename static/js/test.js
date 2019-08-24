odoo.define("accountcore.begin_balance_check1", function (require) {
    "use strict";
    var not = require('bus.BusService');
    $(function () {
        var newnot = new not();
        newnot.endNotification('fsf', 'fsfs', function () {
            alert('424');
        });
        alert('ddd');
    });
    alert('eee');
});

odoo.define("accountcore.begin_balance_check1", function (require) {
    "use strict";
    var testWidget = require('accountcore.begin_balance_check').testWidget;
    var not = require('bus.BusService');
    $(function () {
        var newnot = new not();
        newnot.endNotification('fsf', 'fsfs', function () {
            alert('发送到反倒是大法官');
        });
        var test = new testWidget();
        test.insertAfter($('.ac_balance_check1'));
        test.do_notify('notify', 'notify', true);
        $('.ac_balance_check1').on('click', function () {
            test.getrpc();
        })
        alert('ddd');

    })();
});
