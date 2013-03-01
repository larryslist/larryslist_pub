define(["tools/ajax", "models/collector"], function(ajax, Collector){
    var STORAGE_KEY = 'LS_USER_CART'

    , Collectors = ajax.Collection.extend({
        model:Collector
    })
    , Cart = ajax.Model.extend({
        initialize: function(opts){
            this.register({'Collectors': new Collectors()});

            var data = hnc.options.cart;
            if(data)this.setRecursive(data);
            this.listenTo(this, 'Collectors:add', this.persist);
            this.listenTo(this, 'Collectors:remove', this.persist);
        }
        , persist:function(collector){
            var cart = this;
            ajax.submit({url:"/cart/save", data:this.toJSON(), success: function(){
                cart.trigger.call(cart, "item:changed", collector);
            }});
        }
        , addProfile: function(collector){
            if(!this.contains(collector)){
                this.get("Collectors").add(collector);
                collector.trigger("cart:added");
            }
        }
        , removeProfile: function(collector){
            collector.trigger("cart:removed");
            this.get("Collectors").remove(collector.id);
        }
        , getProfile: function(collector){
            return this.get("Collectors").get(collector.id) || collector;
        }
        , contains: function(collector){
            return !_.isEmpty(this.get("Collectors").get(collector.id))
        }
        , getItems: function(cb, ctxt){
            cb.call(ctxt, this.get("Collectors")||[]);
        }
        , canSpend: function(user, cb, ctxt){
            this.getItems(function(items){
                 cb.call(ctxt, items.length>0 && user.getCredits() >= items.length);
            })
        }
    })

    , cart = new Cart();
    return cart;
});