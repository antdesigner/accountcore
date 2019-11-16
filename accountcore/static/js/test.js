$(function () {
    window.οnscrοll = function () {
        var top1 = document.body.scrollTop;
        if (top1 >= 300)
            $(".jexcel_toolbar").css("position", "absolute").css("top", top1);
        else
            $(".jexcel_toolbar").css("position", "absolute").css("top", 300);
    };
});