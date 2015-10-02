function HTMLAcademyXBlockStudentView(runtime, element) {

    var urls = {
        start: runtime.handlerUrl(element, 'start_lab'), // +
        check: runtime.handlerUrl(element, 'check_lab'), // +
        get_state: runtime.handlerUrl(element, 'staff_info'), // +
        reset_state: runtime.handlerUrl(element, 'reset_user_data'), // +
        get_current_state: runtime.handlerUrl(element, 'get_current_user_data'),
        check_no_auth: runtime.handlerUrl(element, 'check_lab_external', '', '', true),
        get_tasks_data: runtime.handlerUrl(element, 'get_tasks_data')
    };

    var id = $(element).data('id');

    var deplainify = function(obj) {
        for (var key in obj) {
            try {
                if (obj.hasOwnProperty(key)) {
                    obj[key] = deplainify(JSON.parse(obj[key]));
                }
            } catch (e) {
                console.log('failed to deplainify', obj);
            }
        }
        return obj;
    };

    function enable_controls(enabled)
    {
        var action_bar = $(element).find(".action");
        action_bar.data("disabled", enabled);
        if (enabled) {
            action_bar.find("input").removeClass("disabled").attr("disabled", false);
        } else {
            action_bar.find("input").addClass("disabled").attr("disabled", "disabled");
        }
    }

    function disable_controllers(context)
    {
        $(context).find("input").addClass('disabled').attr("disabled", "disabled");
    }

    function enable_controllers(context)
    {
        $(context).find("input").removeClass('disabled').removeAttr("disabled");
    }

    function render(data)
    {
        var xblock = $(element).find('.ifmo-xblock-student');
        var template = _.template(xblock.find('script.ifmo-xblock-template-base').text());
        xblock.find('.ifmo-xblock-content').html(template(data));
        render_bind();
    }

    function render_bind(){

        $(element).find('.staff-get-state-btn').off('click').on('click', function(e) {
            disable_controllers(element);
            var data = {
                'user_login': $(element).find('input[name="user"]').val()
            };
            $.ajax({
                url: urls.get_state,
                type: "POST",
                data: JSON.stringify(data),
                success: function(data){
                    var state = deplainify(data);
                    $(element).find('.staff-info-container').html('<pre>' + JSON.stringify(state, null, '  ') + '</pre>');
                },
                complete: function(data) {
                    console.info('staff-get-state-btn', data);
                    enable_controllers(element);
                }
            });
        });

        $(element).find('.staff-reset-state-btn').off('click').on('click', function(e) {
            if (!confirm('Do you really want to reset state?')) {
                return;
            }
            disable_controllers(element);
            var data = {
                'user_login': $(element).find('input[name="user"]').val()
            };
            $.ajax({
                url: urls.reset_state,
                type: "POST",
                data: JSON.stringify(data),
                success: function(data) {
                    var state = deplainify(data);
                    $(element).find('.staff-info-container').html('<pre>' + JSON.stringify(state, null, '  ') + '</pre>');
                },
                complete: function(data){
                    console.info('staff-reset-state-btn', data);
                    enable_controllers(element);

            }});
        });

        $(element).find('.staff-update-state-btn').off('click').on('click', function(e) {
            disable_controllers(element);
            var data = {
                'user_login': $(element).find('input[name="user"]').val()
            };
            $.ajax({
                url: urls.check,
                type: "POST",
                data: JSON.stringify(data),
                success: function(data) {
                    var state = deplainify(data);
                    $(element).find('.staff-info-container').html('<pre>' + JSON.stringify(state, null, '  ') + '</pre>');
                },
                complete: function(data) {
                    console.info('staff-update-state-btn', data);
                    enable_controllers(element);
                }
            });
        });

    }

    function init_xblock($, _)
    {
        var xblock = $(element).find('.ifmo-xblock-student');
        var data = xblock.data('student-state');
        render(data);

        $(xblock).on("click", ".ant-start-lab", function(e){
            window.location=urls.start;
        });

        $(xblock).on("click", ".ant-check-lab", function(e){
            enable_controls(false);
            $.ajax({
                url: urls.check,
                type: 'POST',
                data: '{}',
                dataType: 'json',
                success: function(data) {
                    var dataJSON = JSON.parse(data);
                    render(JSON.parse(dataJSON.student_state));
                    if (dataJSON.error != ''){
                        $(".htmlacademy-error").show();
                        $(".htmlacademy-error-text").html(dataJSON.error);
                    }
                },
                error: function() {
                },
                complete: function() {
                    enable_controls(true);
                }
            })
        });
    }

    function renderStaffInfo(data){
        var template = _.template($(element).find("#staff-info-main").text());
        $("#staff-info").html(template(data));

        $(element).find("#ifmo-xblock-submit").click(function(event){
            event.preventDefault();
            $.ajax({
                url: staffInfoUrl,
                type: "POST",
                success: renderStaffInfo,
                data: JSON.stringify({"user": $(element).find("#ifmo-xblock-username").val()})
            });
        });
    }

    $(function(){
        init_xblock($, _);
        var block = $(element).find(".ifmo-xblock-student");
        var is_staff = block.attr("data-is-staff") == "True";
        if (is_staff) {
            $('.instructor-info-action').leanModal();
            $(element).find('.staff-info-grades-data').text(block.data('url-grades-data'));
        }
    });

}