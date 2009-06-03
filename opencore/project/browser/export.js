  var exportEnabled = true;
  // We should probably start checking state  on page load,
  // in case multiple people visit the url or you come back later after
  // starting a VERY slow job...
  $(document).ready(function() {
    $("#project-export").submit(function() {
      if (exportEnabled) {
        $("#project-export-status").addClass("active").empty().append('Exporting project... <span id="currently-exporting"></span>');
        $("#project-export input[type='submit']").attr("disabled", "true");
        exportEnabled = false;
        // url and data should be updated (probably also type and data)
        $.ajax({
              url: 'export/do_export',
              type: "post",
              data: ({ s: "stuff goes here", format: "ajax" }),
              dataType: "html",
              success: function(msg){
                  $("#project-export").everyTime(4000, "status", function() { //first arg is millisecs, so this will probably need to be revised
		    $.getJSON('export/current_status_json', function(data) {
		      if (data.state == "finished")  {
                          $('#project-export').stopTime("status");
                          $("#project-export-status").empty().append('Finished!').removeClass("active");
                          $("#project-export-list-header").removeClass("oc-hidden");
                          $("#project-export input[type='submit']").removeAttr("disabled");
                          $("#project-export-list").prepend('<li><a href="export/' + data.filename + '">' + data.filename + '</a>');

                          exportEnabled = true;
                      }
		      else if (data.state == "failed")  {
                          $('#project-export').stopTime("status");
                          $("#project-export-status").empty().removeClass("active").append('Failure of some sort');
                          $("#project-export input[type='submit']").removeAttr("disabled");
                          exportEnabled = true;
                      }
                      else if (data.progress != '' ) {
                           $('#currently-exporting').empty().append(data.state + ': ' + data.progress);
                      }
                      else {
                          $('#currently-exporting').empty().append(data.state);
		      };
                    });
                  });
              },
              error: function(XMLHttpRequest, textStatus, errorThrown){
                 $('#currently-exporting').empty().append(errorThrown);
                 $("#project-export-status").removeClass("active");
                 $("#project-export input[type='submit']").removeAttr("disabled");
                 exportEnabled = true;
              }
           }
        );
        return false;
      }
      alert("We're running an export already! Please be patient.");
      return false;
    });
  });
