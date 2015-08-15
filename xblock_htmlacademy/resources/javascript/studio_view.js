function HTMLAcademyXBlockStudioView(runtime, element)
{

    var saveUrl = runtime.handlerUrl(element, 'save_settings');

    function save()
    {
        var view = this;
        view.runtime.notify('save', {state: 'start'});

        var data = {};
        $(element).find(".input").each(function(index, input) {
            data[input.name] = input.value;
        });

        $.ajax({
            type: "POST",
            url: saveUrl,
            data: JSON.stringify(data),
            success: function() {
                view.runtime.notify('save', {state: 'end'});
            }
        });
    }

    function init_xblock($, _)
    {
        var xblock = $(element).find('.ifmo-xblock-editor');
        var data = xblock.data('metadata');
        var template = _.template(xblock.find('.ifmo-xblock-template-base').text());
        xblock.find('.ifmo-xblock-content').html(template(data));
    }

    $(function(){
       init_xblock($, _);
    });

    return {
        save: save
    }

}