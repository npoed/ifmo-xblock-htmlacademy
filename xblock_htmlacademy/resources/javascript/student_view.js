function HTMLAcademyXBlockStudentView(runtime, element)
{

    var checkUrl = runtime.handlerUrl(element, 'check_lab');
    var startUrl = runtime.handlerUrl(element, 'start_lab');

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

    function render(data)
    {
        var xblock = $(element).find('.ifmo-xblock-student');
        var template = _.template(xblock.find('script.ifmo-xblock-template-base').text());
        xblock.find('.ifmo-xblock-content').html(template(data));
    }

    function init_xblock($, _)
    {
        var xblock = $(element).find('.ifmo-xblock-student');
        var data = xblock.data('student-state');
        render(data);

        $(xblock).on("click", ".ant-start-lab", function(e){
            window.location=startUrl;
        });

        $(xblock).on("click", ".ant-check-lab", function(e){
            enable_controls(false);
            $.ajax({
                url: checkUrl,
                type: 'POST',
                data: '{}',
                dataType: 'json',
                success: function(data) {
                    render(JSON.parse(JSON.parse(data).student_state));
                },
                error: function() {
                },
                complete: function() {
                    enable_controls(true);
                }
            })
        });
    }

    $(function(){
        init_xblock($, _);
    });

}