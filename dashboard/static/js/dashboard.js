dashboard = {
    showNotification: function(from, align, type, message) {

        $.notify({
            icon: "notifications",
            message: message

        }, {
            type: type,
            timer: 4000,
            placement: {
                from: from,
                align: align
            }
        });
    }

}