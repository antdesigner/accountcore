if (!accountcore.web.web_client) {
    odoo.define('accountcore.web.web_client', function (require) {
            var Fast_period = require('accountcore.fast_period')
            var fast_period = new Fast_period();

            $(function () {
                    fast_period.appendTo($("[name='endDate']"));
                });

            });
    }
    else {

    };