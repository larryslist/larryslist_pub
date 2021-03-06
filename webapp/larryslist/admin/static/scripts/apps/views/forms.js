/**
 * Created with PyCharm.
 * User: Martin
 * Date: 24.01.13
 * Time: 14:20
 * To change this template use File | Settings | File Templates.
 */
define(['tools/ajax', "libs/fileupload", "libs/typeahead", "libs/tagsearch"], function(ajax, FileUploader, TypeAhead, TagSearch){
    var View = Backbone.View.extend({
        events: {
            "click .remove-link": "removeRow"
            , "keyup .remove-link": "removeRow"
            , "click .add-more-link" :"addRow"
            , "keyup .add-more-link": "addRow"
        }
        , removeLink: '<a class="remove-link link close">&times;</a>'
        , initialize: function(opts){
            var view = this;
            var valid_params = {form: this.$el};

            ajax.ifyForm(_.extend(valid_params, opts.validatorOpts));

            this.wrapperSelector = opts.wrapperSelector || '[data-closure="form"], .form-validated';
            this.templateSelector = opts.templateSelector || "[data-sequence], .form-validated";

            this.$el.find(this.wrapperSelector).each(function(idx, elem){
                var required = $(elem).data("required") === true;
                $(elem).find(view.templateSelector).each(function(idx, elem){
                    if(idx>0)$(elem).prepend(view.removeLink);
                });
            });

            this.widgets = [];
            this.setupWidgets(this.$el);

            this.saveTimeout = null;
            this.savedTimeout = null;
            this.$el.on({
                change: function(){
                    view.saveTimeout && clearTimeout(view.saveTimeout);
                    view.saveTimeout = setTimeout(function(){
                        view.$el.submit();
                    }, 90000);
                }
                , "form:saved": function(){
                    view.saveTimeout && clearTimeout(view.saveTimeout);
                    view.savedTimeout && clearTimeout(view.savedTimeout);
                    view.$el.addClass("data-saved");
                    view.savedTimeout = setTimeout(function(){
                        view.$el.removeClass("data-saved");
                    }, 4000);

                }
            });
        }
        , setupWidgets : function(el){
            el.find(".typeahead-container").each(_.bind(this.addTypeAhead, this));
            el.find(".tagsearch-container").each(_.bind(this.addTagSearch, this));
            el.find(".dependent-control").each(_.bind(this.addDependent, this));
            el.find(".file-upload-control").each(_.bind(this.addFileUpload, this));
            el.find(".typed-upload-control").each(_.bind(this.addTypedFileUpload, this));
            el.find(".custom-control").each(_.bind(this.addCustomControl, this));
        }
        , addCustomControl: function(idx, elem){
            var data = $(elem).data();
            data.el = elem;
            require([data.customModule], function(V){V.init(data)});
        }
        , addDependent: function(idx, elem){
            var $target = $(elem), data = $target.data(), wrapper = $target.closest(this.templateSelector), depSrc = wrapper.find('[name$='+data.dependency+']')
                , f = function(t){
                    var val = new RegExp(t.find("option").filter(":selected").val()||'hide-at-all-costs');
                    if(val.test(data.dependencyValue)){
                        $target.show();
                    } else {
                        $target.hide().find("input").val("");
                    }
                };
            depSrc.on("change.dependent-fields", function(e){f($(e.target))});
            f(depSrc);
        }
        , addTagSearch: function(idx, elem){
            var data = _.extend({el:elem}, $(elem).data());
            if(data.customModule)
                require([data.customModule], function(V){
                    V.init(data);
                });
            else TagSearch.init(data);
        }
        , addTypeAhead: function(idx, elem){
            TypeAhead.init(_.extend({el:elem}, $(elem).data()));
        }
        , addFileUpload: function(idx, elem){
            var fpl = new FileUploader({el: elem});
            fpl.on("file:uploaded", function(file_path, file){
                var path = hnc.resUrl(file_path);
                $(elem).find(".profile-picture").remove();
                $(elem).find(".picture-holder").val(file_path).after('<div class="img-wrap profile-picture img-polaroid"><div class="img-wrap-inner"><img src="'+path+'" class="picture"/></div></div>');
            })
        }
        , addTypedFileUpload: function(idx, elem){
            var view = this
                , fpl = new FileUploader({el: elem})
                , $elem = $(elem)
                , fileTemplate = _.template($elem.find(".file-template").html())
                , imgTemplate = _.template($elem.find(".image-template").html());
            fpl.on("file:uploaded", function(file_path, file){
                var tmpl = (hnc.isPicturePath(file_path)?imgTemplate:fileTemplate)
                    , pos = this.$(".typed-uploaded-file").length;
                    this.$el.append(tmpl({name:file.name, fullPath:hnc.resUrl(file_path), path:file_path, pos:pos}));
            });
            $elem.on(hnc.support.clickEvent, ".close", function(e){
                $(e.currentTarget).closest(".form-validated").trigger("change");
                $(e.currentTarget).closest(".typed-uploaded-file").remove();

                var reIdx = function(elem, pos){
                    _.each(['id','name'], function(attr){
                        if(elem.attr(attr))
                            elem.attr(attr, elem.attr(attr).replace(/-[0-9]+\./g, "-"+pos+"."))
                    });
                };
                $elem.find(".typed-uploaded-file").each(function(idx, row){
                    $(row).find("input").each(function(i, input){reIdx($(input), idx)});
                });
            });
        }
        , addRow : function(e){
            if((!e.keyCode || e.keyCode == 13)){
                var $target = $(e.target)
                    , templ = $target.closest(this.wrapperSelector).find(this.templateSelector).last()
                    , new_node = templ.clone()
                    , new_position = parseInt(templ.data("sequence"), 10) + 1
                    , inc = function(elem, attr){
                        if(elem.attr(attr))
                            elem.attr(attr, elem.attr(attr).replace(/-[0-9]+\./g, "-"+new_position+"."))
                    };
                new_node.find("input,select,textarea").each(function(index, elem){
                    elem = $(elem);
                    inc(elem, "id");
                    inc(elem, "name");
                    if(!elem.is('[type=checkbox],.typehead-token,[readonly]'))elem.val("");
                });
                new_node.removeAttr("data-sequence").attr("data-sequence", new_position);
                if(!new_node.find(".remove-link").length) new_node.prepend(this.removeLink);
                new_node.find(".numbering").html(new_position+1);

                if($target.data("appendFirst")){
                    templ.closest(this.wrapperSelector).prepend("<hr/>").prepend(new_node);
                    $target.hide();
                } else {
                    templ.after(new_node);
                }
                new_node.trigger("change");

                new_node.find("[generated]").remove();
                new_node.find(".error").removeClass("error");
                new_node.find(".valid").removeClass("valid");

                this.setupWidgets(new_node);
            }
        }
        , removeRow : function(e){
            if(!e.keyCode|| e.keyCode == 13){
                var $target = $(e.target), $embeddedForm = $target.closest(this.templateSelector)
                    , siblings = $embeddedForm.siblings(this.templateSelector)
                    , idx = function(elem, pos){
                        _.each(['id','name'], function(attr){
                            if(elem.attr(attr))
                                elem.attr(attr, elem.attr(attr).replace(/-[0-9]+\./g, "-"+pos+"."))
                        });
                    };
                $embeddedForm.trigger("change");
                $embeddedForm.remove();
                siblings.each(function(i, elem){
                    $(elem).attr('data-sequence', i).find("input,select,textarea").each(function(k, e){
                            idx($(e), i);
                    });
                    $(elem).find(".numbering").html(i+1);
                });

            }
        }
    });
    return View;
});