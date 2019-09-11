// 凭证借贷方金额
odoo.define('accountcore.accountcoreListRenderer', function (require) {
    "use strict";
    var ListRenderer = require('web.ListRenderer');

    ListRenderer.include({
        events: _.extend({}, ListRenderer.prototype.events, {
            'change table td.voucher_d_amount': '_entryamountChange',
            'change table td.voucher_c_amount': '_entryamountChange',
        }),
        _entryamountChange: function (event) {
            // table td.voucher_c_amount 的元素改变事件处理
        },
        init: function (parent, state, params) {
            var self = this;
            this._super.apply(this, arguments);
        },
        _renderBodyCell: function (record, node, colIndex, options) {
            var self = this;
            var newTd = this._super.apply(this, arguments);
            // 如果给字段添加了class="amountColor"属性,那么这个字段为金额字段显示的值改变颜色
            var name = node.attrs.name;
            var amount = record.data[name];
            if (_hasClass(newTd, 'amountColor')) {
                _changeNodeColor(newTd, amount);
            };
            return newTd;
        }
    });
    //改变金额节点颜色
    function _changeNodeColor(node, amount) {
        switch (true) {
            case (amount - 0 > 0):
                break;
            case (amount - 0 == 0):
                node.addClass('amount-zero');
                // css定义在 server\addons\accountcore\static\css\accountcore.css
                break;
            case (amount - 0 < 0):
                node.addClass('amount-negative');
                break;
            default:
                break;
        }
        return node;
    };

    //含有类
    function _hasClass(td, className) {
        if (td.hasClass(className)) {
            return true;
        };
        return false;
    };
    return ListRenderer;
});
//凭证的核算项目字段
odoo.define('web.accountcoreExtend', ['web.basic_fields', 'web.relational_fields', 'accountcore.accountcoreVoucher', 'web.field_registry'], function (require) {
    "use strict";
    var relational_fields = require('web.relational_fields');
    var fieldMany2ManyTags = relational_fields.FieldMany2ManyTags;
    var accountcoreVoucher = require('accountcore.accountcoreVoucher');
    var FieldChar = require('web.basic_fields').FieldChar;
    var tiger_accountItems_m2m = fieldMany2ManyTags.extend({

        activate: function () {
            return this.choiceItemsModel ? this.choiceItemsModel.activate() : false;
        },
        getFocusableElement: function () {
            return this.choiceItemsModel ? this.choiceItemsModel.getFocusableElement() : $();
        },

        /**
         * @private
         */
        _renderEdit: function () {
            var self = this;
            var newAccountId = 0;
            var preAccountId = 0;
            if (this.record.data.account && this.record.data.account.data.id) {
                newAccountId = this.record.data.account.data.id;
            };
            if (this.choiceItemsModel) {
                preAccountId = this.choiceItemsModel.ac_accountId;
                if (preAccountId == newAccountId) {
                    return;
                }
                this.choiceItemsModel.destroy();
            };
            this.choiceItemsModel = new accountcoreVoucher.choiceItemsModel(this, this.name, this.record, {
                mode: 'edit',
                noOpen: true,
                viewType: this.viewType,
                attrs: this.attrs,
            }, newAccountId);
            this.choiceItemsModel.value = false;
            return this.choiceItemsModel.appendTo(this.$el);
        },
        willStart: function () {
            return this._super.apply(this, arguments);
        },
        _onFieldChanged: function (ev) {
            if ($.inArray(ev.target, this.choiceItemsModel.ac_choiceItemsMany2ones) == -1) {
                return;
            };
            ev.stopPropagation();
            var newValue = ev.data.changes[this.name];
            if (newValue) {
                //改变了核算项目,例如:以前是A,现在选择了B
                this._addTag(newValue);
                var id = ev.target.ac_itemId;
                if (id && id > 0 && id != newValue.id) {
                    this._removeTag(id);
                }

                ev.target.ac_itemId = newValue.id;
                ev.target.ac_itemName = newValue.display_name;
                //重要覆写
                ev.stopPropagation();
                return;
            };
            //没有选择,或删除了核算项目,以前是A现在删除了A,没有选择其他的
            if (ev.target.ac_itemId) {
                this._removeTag(ev.target.ac_itemId);
            }
            ev.target.ac_itemId = null;
            ev.target.ac_itemName = null;

            //重要覆写
            ev.stopPropagation();
        },

    });
    var FieldChar_voucher_explain = FieldChar.extend({
        events: _.extend({}, FieldChar.prototype.events, {
            'focusin': '_onBlur',
        }),
        _onBlur: function (e) {
            var self = $(e.target)
            var pr_tr = self.parentsUntil('tr').parent('tr').prev('tr');
            var pr_explain = pr_tr.find('span.oe_ac_explain');
            var explain = self.val();
            if ($.trim(explain) == '') {
                self.val(pr_explain.text());
                self.trigger('input');
            };
        },
    });

    var FieldMany2ManyCheckBoxes = relational_fields.FieldMany2ManyCheckBoxes;
    var FieldMany2ManyCheckBoxes_flowToLeft = FieldMany2ManyCheckBoxes.extend({
        template: 'FieldMany2ManyCheckBoxes_flowToLeft',
    });
    var fieldRegistry = require('web.field_registry');
    fieldRegistry.add('tiger_accountItems_m2m', tiger_accountItems_m2m);
    // 继承many2many_checkboxes向左浮动
    fieldRegistry.add('many2many_checkboxes_floatleft', FieldMany2ManyCheckBoxes_flowToLeft);
    fieldRegistry.add('FieldChar_voucher_explain', FieldChar_voucher_explain);

    return {
        tiger_accountItems_m2m: tiger_accountItems_m2m,
        fieldMany2ManyCheckBoxes_flowToLeft: FieldMany2ManyCheckBoxes_flowToLeft,
        FieldChar_voucher_explain: FieldChar_voucher_explain,
    };
});
//凭证的核算项目字段选择
odoo.define('accountcore.accountcoreVoucher', ['web.AbstractField', 'web.relational_fields', 'web.field_registry', 'web.core', 'web.field_utils'], function (require) {
    "use strict";
    var AbstractField = require('web.AbstractField');
    var relational_fields = require('web.relational_fields');
    var FieldMany2One = relational_fields.FieldMany2One;
    var core = require('web.core');
    var qweb = core.qweb;
    var field_utils = require('web.field_utils');
    var _t = core._t;
    var ChoiceItemsMany2one = FieldMany2One.extend({
        events: _.extend({}, FieldMany2One.prototype.events, {
            'blur input': '_onBlur',
            'keydown input': '_onKeydown',

        }),
        _onBlur: function (e) {},

        /**输入时按tab键,跳到下一个项目
         * @param  {} e
         */
        _onKeydown: function (e) {
            self = this;
            e.stopImmediatePropagation();
            switch (e.which) {
                case $.ui.keyCode.TAB:
                    $('.itemChoice').nextUntil('.o_input').first().focus();
                    break;
                default:
                    self._super.apply(self, arguments);
            }
        },
        init: function (parent, name, record, options, typeId, itemName, itemId) {
            this.ac_itemTypeId = typeId;
            this.ac_itemName = itemName;
            this.ac_itemId = itemId;
            // this.ac_valueItemId = itemId;
            this.ac_newItemName = itemName;
            this.ac_newItemId = itemId;
            this.ac_lastSetValueItemId = undefined;
            this._super.apply(this, arguments);
            if (itemName) {
                this.m2o_value = itemName;
            } else {
                this.m2o_value = "";
            };

        },
        start: function () {
            this._super.apply(this, arguments);

        },
        _formatValue: function (value) {

            if (this.ac_itemName) {
                return this.ac_itemName;
            };
            return "";

        },
        _search: function (search_val) {
            var self = this;
            var def = $.Deferred();
            this.orderer.add(def);
            var context = this.record.getContext(this.recordParams);
            var domain = this.record.getDomain(this.recordParams);
            _.extend(context, this.additionalContext);

            var blacklisted_ids = this._getSearchBlacklist();
            if (blacklisted_ids.length > 0) {
                // domain.push(['id', 'not in', blacklisted_ids]);

            }
            //使核算项目下拉列表只选择对应类别
            domain.push(['itemClass', '=', this.ac_itemTypeId]);
            this._rpc({
                    model: this.field.relation,
                    method: "name_search",
                    kwargs: {
                        name: search_val,
                        args: domain,
                        operator: "ilike",
                        limit: this.limit + 1,
                        context: context,
                    }
                })
                .then(function (result) {
                    var values = _.map(result, function (x) {
                        x[1] = self._getDisplayName(x[1]);
                        return {
                            label: _.str.escapeHTML(x[1].trim()) || data.noDisplayContent,
                            value: x[1],
                            name: x[1],
                            id: x[0],
                        };
                    });

                    // search more... if more results than limit
                    if (values.length > self.limit) {
                        values = values.slice(0, self.limit);
                        values.push({
                            label: _t("Search More..."),
                            action: function () {
                                self._rpc({
                                        model: self.field.relation,
                                        method: 'name_search',
                                        kwargs: {
                                            name: search_val,
                                            args: domain,
                                            operator: "ilike",
                                            limit: 160,
                                            context: context,
                                        },
                                    })
                                    .then(self._searchCreatePopup.bind(self, "search"));
                            },
                            classname: 'o_m2o_dropdown_option',
                        });
                    }
                    var create_enabled = self.can_create && !self.nodeOptions.no_create;
                    // quick create
                    var raw_result = _.map(result, function (x) {
                        return x[1];
                    });
                    if (create_enabled && !self.nodeOptions.no_quick_create &&
                        search_val.length > 0 && !_.contains(raw_result, search_val)) {
                        values.push({
                            label: _.str.sprintf(_t('Create "<strong>%s</strong>"'),
                                $('<span />').text(search_val).html()),
                            action: self._quickCreate.bind(self, search_val),
                            classname: 'o_m2o_dropdown_option'
                        });
                    }
                    // create and edit ...
                    if (create_enabled && !self.nodeOptions.no_create_edit) {
                        var createAndEditAction = function () {
                            // Clear the value in case the user clicks on discard
                            self.$('input').val('');
                            return self._searchCreatePopup("form", false, self._createContext(search_val));
                        };
                        values.push({
                            label: _t("Create and Edit..."),
                            action: createAndEditAction,
                            classname: 'o_m2o_dropdown_option',
                        });
                    } else if (values.length === 0) {
                        values.push({
                            label: _t("No results to show..."),
                        });
                    }

                    def.resolve(values);
                });

            return def;
        },

        _onFieldChanged: function (event) {
            this.lastChangeEvent = event; //test
            var newItem = event.data.changes.items;
            this.ac_newItemName = newItem.display_name;
            this.ac_newItemId = newItem.id;
            this.$input.val(this.ac_newItemName);
        },

    });
    var choiceItemsModel = AbstractField.extend({
        //凭证中的选择核算项目
        supportedFieldTypes: ['many2many'],
        template: 'accountcore_voucher_choice_items',

        custom_events: _.extend({}, AbstractField.prototype.custom_events, {

        }),
        events: _.extend({}, AbstractField.prototype.events, {

        }),

        init: function (parent, name, record, options, accountId) {
            this._super.apply(this, arguments);
            this.limit = 8;
            this.ac_items = []; //分录已有的核算项目
            this.ac_accountId = accountId;
            this.ac_choiceItemsMany2ones = [];
        },


        /**
         * 加载和设置分录核算项目
         * @returns {Deferred}
         */
        _initItems: function () {
            var self = this;
            return $.when(this._getEntryItems()).then(function (items) {
                self.ac_items = items;
            });
        },
        start: function () {
            var self = this;
            self.itemChoiceContainer = this.$el;
            return this._super.apply(this, arguments);

        },

        reinitialize: function (value) {
            this.isDirty = false;
            this.floating = false;
            return this._setValue(value);
        },
        /**获得对应核算项目类别的核算项目
         * @return {string} 项目名称
         */
        _getItem: function (items, typeId) {
            var item = {};
            $.each(items, function (i, n) {
                if (items[i].itemClass == typeId) {
                    item.name = items[i].name;
                    item.id = items[i].id;
                    return false;
                };
            });
            return item;
        },
        /**核算项目栏插入一个many2one部件
         * @param  {object} itemType 核算项目对象
         * @param  {object} container 凭证分录中的核算项目栏
         */
        _insertItemChoice: function (itemType, container) {
            var self = this;
            var typeName = itemType.name;
            var typeId = 'itemType_' + itemType.id;
            var attrs = this.attrs;
            var item = self._getItem(self.ac_items, itemType.id);

            var oneItemChoice = new ChoiceItemsMany2one(self, self.name, self.record, {
                mode: 'edit',
                noOpen: true,
                viewType: self.viewType,
                attrs: attrs,
            }, itemType.id, item.name, item.id);

            var itemsIds = $.map(self.ac_items, function (i) {
                return i.id;
            });
            oneItemChoice._getSearchBlacklist = function () {
                return itemsIds || [];
            };
            var itemRow = $(self._createItemChoiceHtml(typeName));
            itemRow.appendTo(container);
            var seletiontag = itemRow.find('.ac-item-selection').first();
            oneItemChoice.appendTo(seletiontag);
            self.ac_choiceItemsMany2ones.push(oneItemChoice);
            oneItemChoice.$el.find('input').attr('id', typeId);
        },
        /**获取科目下挂的核算项目类别
         * @param  {integer} accountId 科目ID
         * @returns {object} 核算项目类别列表[{'id':,'name':}]
         */
        _getItemTypes: function (accountId) {
            return this._rpc({
                model: 'accountcore.account',
                method: 'get_itemClasses',
                args: [accountId]
            });

        },
        /**构建核算项目类别标签
         * @param  {string} itemTypeName 核算项目类别名称
         */
        _createItemChoiceHtml: function (itemTypeName) {
            var htmlstr = "<div class='row itemChoice'><div class='col-3 ac-item-type-name'>" + itemTypeName + "</div><div class='ac-item-selection'></div></div>";
            return htmlstr;
        },
        _removeTag: function (id) {
            var record = _.findWhere(this.value.data, {
                res_id: id
            });
            this._setValue({
                operation: 'FORGET',
                ids: [record.id],
            });
        },
        _renderEdit: function () {
            var self = this;
            $.each(self.itemTypes, function (i) {
                self._insertItemChoice(self.itemTypes[i], self.itemChoiceContainer);
            });
        },
        willStart: function () {
            var self = this;
            var def1 = self._super.apply(this, arguments);
            var def2 = self._getItemTypes(self.record.data.account.res_id);
            var def3 = def2.then(function (param) {
                self.itemTypes = param;
            });
            var def4 = self._initItems();
            return $.when(def1, def2, def3, def4);
        },
        _getRenderTagsContext: function () {
            return {
                itemTypes: this.itemTypes,
            };
        },
        /**获得分录的核算项目列表
         * @param  {integer} entryId 分录ID
         * @return {obj} 核算项目列表{id:,name:,itemClass:}
         */
        _getEntryItems: function () {
            var entryId = this.record.data.items.res_ids;
            return this._rpc({
                model: 'accountcore.item',
                method: 'getEntryItems',
                args: [entryId]
            });
        },
        getFocusableElement: function () {
            return this.mode === 'edit' && this.$('input').first() || this.$el;
        },
    });
    var fieldRegistry = require('web.field_registry');
    fieldRegistry.add('choiceItemsModel', choiceItemsModel);
    return {
        ChoiceItemsMany2one: ChoiceItemsMany2one,
        choiceItemsModel: choiceItemsModel,

    }
});
//给凭证列表视图添加按钮
odoo.define('accountcore.accountcoreVoucheListButton', function (require) {
    "use strict";
    var ListView = require('web.ListView');
    var viewRegistry = require('web.view_registry');
    var ListController = require('web.ListController');
    var voucherListController = ListController.extend({
        renderButtons: function () {
            this._super.apply(this, arguments);
            if (this.$buttons) {
                var btns = this.$buttons;
                var ac_voucher_number_sort_btn = btns.find('.ac_voucher_number_sort'); //凭证编号排序按钮
                ac_voucher_number_sort_btn.on('click', this.proxy('vouchersSortByNumber'));
                var ac_voucher_filter_btn = btns.find('.ac_voucher_filter'); //查询按钮
                ac_voucher_filter_btn.on('click', this.proxy('voucher_filter'));
            };
        },
        /**依据凭证编号对凭证列表进行排序
         */
        vouchersSortByNumber: function () {
            var tbody = this.$el.find('tbody').first();
            var trs = this.$el.find('tr.o_data_row');
            trs.detach();
            trs.sort(this._voucherNumbersort);
            tbody.append(trs);

        },
        _voucherNumbersort: function (a, b) {
            return $(a).find('.voucherNumber').text() - $(b).find('.voucherNumber').text();
        },
        //查询凭证
        voucher_filter: function () {
            alert('暂未实现');
        },
    });
    var voucherListView = ListView.extend({
        config: _.extend({}, ListView.prototype.config, {
            Controller: voucherListController,
        }),
    });
    viewRegistry.add('voucherListView', voucherListView);
    return voucherListView;
});
//启用期初列表视图
odoo.define('accountcore.balanceListView', function (require) {
    "use strict";
    var ListView = require('web.ListView');
    var viewRegistry = require('web.view_registry');
    var ListController = require('web.ListController');
    var CheckBalance = require('accountcore.begin_balance_check');
    var balanceListController = ListController.extend({
        renderButtons: function () {
            this._super.apply(this, arguments);
            if (this.$buttons) {
                var btns = this.$buttons;
                var check_balance_btn = new CheckBalance(this);
                check_balance_btn.appendTo(btns);
            };
        },

    });
    var balanceListView = ListView.extend({
        config: _.extend({}, ListView.prototype.config, {
            Controller: balanceListController,
        }),
    });
    viewRegistry.add('balanceListView', balanceListView);
    return balanceListView;
});
//启用期初平衡检查按钮
odoo.define("accountcore.begin_balance_check", function (require) {
    "use strict";
    var Widget = require('web.Widget');
    var framework = require('web.framework');
    var CheckBalance = Widget.extend({
        template: 'accountcore.check_balance',
        events: {
            'click': '_do_check',
        },
        _do_check: function () {
            var self = this;
            this.do_action({
                name: '启用期初平衡检查',
                type: 'ir.actions.act_window',
                res_model: 'accountcore.begin_balance_check',
                views: [
                    [false, 'form']
                ],
                target: 'new'
            });
            // framework.blockUI();
            // alert('开始试算平衡');
            // this._rpc({
            //     model: 'accountcore.account',
            //     method: 'get_itemClasses',
            //     args: [176],
            // }).then(function (items) {
            //     // _.map(items,function(){
            //     //     s=s+self.name;
            //     //   });

            //     console.log('over!');
            //     setTimeout(function () {
            //         framework.unblockUI();
            //         self.do_notify('结果', '该功能还在开发中!');
            //     }, 5000);

            // }, function () {
            //     console.log('error!');
            //     FrameWork.unbolckUI();
            // });
        },

    });
    return CheckBalance;
});
// 快速选取期间
odoo.define("accountcore.fast_period", ['web.AbstractField', 'web.field_registry', 'web.time', 'accountcore.period_tool'], function (require) {
    "use strict";
    var AbstractField = require('web.AbstractField');
    var time = require('web.time');
    var Perod_tool = require('accountcore.period_tool');
    var ac_fast_period = AbstractField.extend({
        supportedFieldTypes: ['date'],
        template: 'accountcore.fast_period',
        attributes: {
            style: "background-color:white;border: 1px solid grey;"
        },
        events: _.extend({}, AbstractField.prototype.events, {
            'click button': '_onClick',
        }),
        _onClick: function (e) {
            var self = this;
            var btn = $(e.target);
            var periodScop = self._getPeriod(btn.text());
            var startDate = $("[name='startDate'] input");
            var endDate = $("[name='endDate'] input");
            startDate.val(time.date_to_str(periodScop.startDate)).trigger('change');
            endDate.val(time.date_to_str(periodScop.endDate)).trigger('change');
        },
        _getPeriod: function (periodName) {
            var dt = new Date();
            var voucherPeriod = new Perod_tool.VoucherPeriod(dt);
            switch (periodName) {
                case '本月':
                    return voucherPeriod.getCurrentMonth();
                case '上月':
                    return voucherPeriod.getPreMonth();
                case '本年':
                    return voucherPeriod.getCurrentYear();
                case '去年':
                    return voucherPeriod.getPreYear();
                case '本季':
                    return voucherPeriod.getCurrentSeason();
                case '上季':
                    return voucherPeriod.getPreSeason();
                case '今年上半年':
                    return voucherPeriod.getFirstHalfYear()
                case '去年上半年':
                    return voucherPeriod.getFirstHalfPreYear();
                case '去年下半年':
                    return voucherPeriod.getSecondHalfPreYear()
                default:
                    return voucherPeriod.getCurrentMonth();

            };
        },
    });
    var fieldRegistry = require('web.field_registry');
    fieldRegistry.add('ac_fast_period', ac_fast_period);
    return {
        ac_fast_period: ac_fast_period,
    };

});
//期间处理工具
odoo.define('accountcore.period_tool', function (require) {
    var Class = require('web.Class');
    //日期范围
    var PeriodScop = Class.extend({
        init: function (startDate, endDate) {
            this.startDate = startDate;
            this.endDate = endDate;
        },
    });
    // 一个会计期间（一个月）
    var VoucherPeriod = Class.extend({
        init: function (date) {
            this.date = date;
            this.year = date.getFullYear();
            this.month = date.getMonth() + 1;
            this.days = this.getDaysOf(this.year, this.month);
            this.firstDate = new Date(this.year, this.month - 1, 1)
            this.endDate = new Date(this.year, this.month - 1, this.days)
        },
        // 当月
        getCurrentMonth: function () {
            return new PeriodScop(this.firstDate, this.endDate);
        },
        // 上月
        getPreMonth: function () {
            var month = this.month - 1;
            var year = this.year;
            if (this.month == 1) {
                month = 12;
                year = year - 1;
            };
            var days = this.getDaysOf(year, month);
            var firstDate = new Date(year, month - 1, 1);
            var endDate = new Date(year, month - 1, days);
            return new PeriodScop(firstDate, endDate);
        },
        getCurrentYear: function () {
            var year = this.year
            var firstDate = new Date(year, 0, 1);
            var days = this.getDaysOf(year, 12);
            var endDate = new Date(year, 11, days);
            return new PeriodScop(firstDate, endDate);

        },
        getPreYear: function () {
            var year = this.year - 1
            var firstDate = new Date(year, 0, 1);
            var days = this.getDaysOf(year, 12);
            var endDate = new Date(year, 11, days);
            return new PeriodScop(firstDate, endDate);
        },
        // 本季
        getCurrentSeason: function () {
            var month = this.month;
            var year = this.year;
            var firstMonth = 10;
            var endMonth = 12;
            if (1 <= month <= 3) {
                firstMonth = 1;
                endMonth = 3;
            } else if (4 <= month < 6) {
                firstrMonth = 4;
                endMonth = 6;
            } else if (7 <= month <= 9) {
                firstrMonth = 7;
                endMonth = 9;
            };
            var days = this.getDaysOf(year, month)
            var firstDate = new Date(year, firstMonth - 1, 1);
            var endDate = new Date(year, endMonth - 1, days);
            return new PeriodScop(firstDate, endDate);

        },
        getPreSeason: function () {
            var month = this.month;
            var year = this.year;
            var firstMonth = 10;
            var endMonth = 12;
            if (1 <= month <= 3) {
                year = this.year - 1
            } else if (4 <= month < 6) {
                firstrMonth = 4;
                endMonth = 6;
            } else if (7 <= month <= 9) {
                firstrMonth = 7;
                endMonth = 9;
            };
            var days = this.getDaysOf(year, endMonth)
            var firstDate = new Date(year, firstMonth - 1, 1);
            var endDate = new Date(year, endMonth - 1, days);
            return new PeriodScop(firstDate, endDate);
        },
        // 上半年
        getFirstHalfYear: function () {
            var year = this.year
            var firstDate = new Date(year, 0, 1);
            var days = this.getDaysOf(year, 6);
            var endDate = new Date(year, 5, days);
            return new PeriodScop(firstDate, endDate);
        },
        getFirstHalfPreYear: function () {
            var year = this.year - 1
            var firstDate = new Date(year, 0, 1);
            var days = this.getDaysOf(year, 6);
            var endDate = new Date(year, 5, days);
            return new PeriodScop(firstDate, endDate);
        },
        getSecondHalfPreYear: function () {
            var year = this.year - 1
            var firstDate = new Date(year, 6, 1);
            var days = this.getDaysOf(year + 1, 0);
            var endDate = new Date(year, 11, days);
            return new PeriodScop(firstDate, endDate);
        },
        getDaysOf: function (year, month) {
            if (month == 12) {
                year = year + 1;
                month = 0;
            }
            return (new Date(year, month, 0)).getDate();
        },
    });
    //连续的会计期间
    var Period = Class.extend({
        init: function (startDate, endDate) {
            this.startDate = startDate;
            this.endDate = endDate;
            this.startYear = startDate.getFullYear();
            this.startMonth = startDate.getMonth() + 1;
            this.endYear = endDate.getFullYear();
            this.endMonth = endDate.getMonth();

        },
        getPeriodList: function () {

        }

    });

    return {
        'VoucherPeriod': VoucherPeriod,
        'PeriodScop': PeriodScop,
        'Period': Period,
    };
});