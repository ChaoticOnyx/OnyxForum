var parent_id_selector = $(".settings-form #parent_id_selector");
var category_id_selector = $(".settings-form #category_id_selector");
var is_subforum = $(".settings-form #is_subforum");

function updateSubforumParentIdSelector() {
    if (is_subforum.is(':checked')) {
        parent_id_selector.show();
        category_id_selector.hide()
    } else {
        parent_id_selector.hide();
        category_id_selector.show()
    }
}

updateSubforumParentIdSelector();

is_subforum.click(updateSubforumParentIdSelector);