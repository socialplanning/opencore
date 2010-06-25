jQuery.noConflict();

function getMemberId(rowEl) {
  var row = jQuery(rowEl).closest("tr");
  var id = row.attr('id');
  return id;
};

function buildForm(memId, memberRole) {
  var action;
  if( memberRole == "administrator" ) {
    action = "demote-admin";
  } else {
    action = "promote-admin";
  };

  var html = "<select name='" + memId + "_role' id='" + memId + "_role'>";
  if( memberRole == "administrator" ) {
    html += "<option value='ProjectAdmin' selected='true'>administrator</option>";
    html += "<option value='ProjectMember'>member</option>";
  } else {
    html += "<option value='ProjectAdmin'>administrator</option>";
    html += "<option value='ProjectMember' selected='true'>member</option>";
  };
  html += "</select>";
  html += "<input style='display:none;' type='submit' value='go' name='task|" + memId + "|" + action + "' />";
  return html;
};

/* return a (role, psm)
   of which either can be null */
function parseResponse(resp) {
    resp = OC.CleanJSON(resp);
    var ret = {"psm": null};

    var memberRole = resp["role"];
    ret["role"] = memberRole;

    var psm = resp["oc-statusMessage-container"];
    if( !psm ) return ret;
    psm = psm["html"];
    if( !psm ) return ret;
    psm = jQuery(psm).find(".oc-statusMessage").text();
    if( !psm ) return ret;

    ret["psm"] = psm;
    return ret;
};

jQuery(document).ready(function() {
	jQuery("tbody#mship-rows td.role input[type='submit']").live("update", function() {
		var button = this;
		var data = jQuery(this).closest("form").serialize();
		var command = jQuery(this).attr("name") + "=" + jQuery(this).attr("value");
		data += "&" + command + "&mode=async";
		var url = jQuery(this).closest("form").attr("action");
		jQuery.post(url, data, function(resp) {
			var memberRole, psm;
			resp = parseResponse(resp);
			if( memberRole = resp["role"] ) {
			    var div = jQuery("<div />").attr("class", memberRole)
				.text(memberRole);
			    jQuery(button).siblings("select").remove();
			    jQuery(button).replaceWith(div);
			    jQuery("#oc-statusMessage-container").children().remove();
			};
			if( psm = resp["psm"] ) {
			    OC.psm(psm, "success");
			};
		    });
		return false;
	    });

	jQuery("tbody#mship-rows td.role div").live("click", function() {
		var memberRole = jQuery(this).attr("class");
		jQuery(this).replaceWith(buildForm(getMemberId(this), memberRole));
	    });

	jQuery("tbody#mship-rows td.role select").live("change", function() {
		jQuery(this).siblings("input[type='submit']").trigger("update");
	    });

    });
