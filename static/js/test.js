$(function () {
    $('.choose_all').on('click', function () {
        var checkboxs = $('[name="org"]').find('[type="checkbox"]');
        if ($(this).text() == '全选') {
            checkboxs.each(function () {
                $(this).prop('checked', true);
                $(this).trigger('change')
            });
            $(this).text("取消");
        } else {
            checkboxs.each(function () {
                $(this).prop('checked', false);
                $(this).trigger('change')
            });
            $(this).text("全选");
        }
    });
});