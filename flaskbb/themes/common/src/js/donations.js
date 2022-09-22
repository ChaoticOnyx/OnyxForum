var issue_row = $(".donation-form #issue_row");
var issue_field = $(".donation-form #issue");
var type_field = $(".donation-form #type");

function updateIssueField() {
    if (type_field.val() == "reject_bounty") {
        issue_row.show();
    } else {
        issue_field.val(0);
        issue_row.hide();
    }
}

updateIssueField();

type_field.change(updateIssueField);
