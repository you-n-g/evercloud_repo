var FormWizard = function () {


    return {
        //main function to initiate the module
        init: function () {
            if (!jQuery().bootstrapWizard) {
                return;
            }
            var form = $('#submit_form');

            form.validate({
                doNotHideMessage: true,
                errorElement: 'span',
                errorClass: 'help-block help-block-error',
                focusInvalid: false,
                rules: {
                    name: {
                        minlength: 7,
                        maxlength: 24,
                        required: true
                    },
                    count: {
                        minlength: 1,
                        required: true
                    },
                    //profile
                    password: {
                        minlength: 8,
                        maxlength: 16,
                        complexPassword: true,
                        required: true
                    },

                    confirm_password: {
                        required: true,
                        equalTo: "#login_password"
                    }
                },
                errorPlacement: function (error, element) {
                    element.parent().append(error);
                },
                highlight: function (element) {
                    $(element).closest('.form-group').removeClass('has-success').addClass('has-error');
                },

                unhighlight: function (element) {
                    $(element).closest('.form-group').removeClass('has-error');
                }
            });



            $('#form_wizard_1 .button-submit').click(function () {
                $("#btnCreateInstance").click();
            });

            $("#img_div").slimScroll({});
        }
    };
}();
