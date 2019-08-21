     $(function () {
         $('[data-toggle="tooltip"]').tooltip();
         var ac_d=$('td[title="ac_dsum"]').get(0);
         var ac_c=$('td[title="ac_csum"]').get(0);
         EventUtil.addHandler(ac_d, "DOMSubtreeModified", sumChange);

     });

     function sumChange() {
         alert('sumChange');
     }