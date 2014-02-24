//http://stackoverflow.com/questions/1184624/convert-form-data-to-js-object-with-jquery
jQuery.fn.serializeObject = function() {
  var arrayData, objectData;
  arrayData = this.serializeArray();
  objectData = {};

  $.each(arrayData, function() {
    var value;

    if (this.value != null) {
      value = this.value;
    } else {
      value = '';
    }

    if (objectData[this.name] != null) {
      if (!objectData[this.name].push) {
        objectData[this.name] = [objectData[this.name]];
      }

      objectData[this.name].push(value);
    } else {
      objectData[this.name] = value;
    }
  });

  return objectData;
};

$(function() {
    tab_history();
/*    $('#zipfile').ajaxfileupload({
        action: '/',
        validate_extensions: false,
        submit_button: $('#go'),
        onStart: function() {
            var elem = $(this);
            var fields = $('#gerber-form').serializeObject();
            elem.before(function() {
              var key, html = '';
              for(key in fields) {
                var paramVal = fields[key];
                if (typeof paramVal === 'function') {
                  paramVal = paramVal();
                }
                html += '<input type="hidden" name="' + key + '" value="' + paramVal + '" />';
              }
              return html;
            });
            console.log(fields);
        }
    });
*/
});

function tab_history(selector) {
    if (selector == undefined) {
        selector = "";
    }
 
    /* Automagically jump on good tab based on anchor */
    $(document).ready(function() {
        url = document.location.href.split('#');
        if(url[1] != undefined) {
            $(selector + '[href=#'+url[1]+']').tab('show');
        }
    });
 
    var update_location = function(event) {
        document.location.hash = this.getAttribute("href");
    }
 
    /* Update hash based on tab */
    $(selector + "[data-toggle=pill]").click(update_location);
    $(selector + "[data-toggle=tab]").click(update_location);
}

