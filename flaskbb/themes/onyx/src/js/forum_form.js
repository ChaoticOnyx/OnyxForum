var subforum_parent_id_selector = $(".settings-form #subforum_parent_id_selector");
var category_id_selector = $(".settings-form #category_id_selector");
var is_subforum = $(".settings-form #is_subforum");

function updateSubforumParentIdSelector() {
    console.log($(".setting-form #category option:selected").val())
    if (is_subforum.is(':checked')) {
        subforum_parent_id_selector.show();
        category_id_selector.hide()
    } else {
        subforum_parent_id_selector.hide();
        category_id_selector.show()
    }
}

updateSubforumParentIdSelector();

is_subforum.click(updateSubforumParentIdSelector);