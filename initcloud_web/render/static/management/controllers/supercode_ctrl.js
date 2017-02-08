CloudApp.controller('SuperCodeController',
    function($rootScope, $scope, $filter, $modal, $i18next, $ngBootbox,
             CommonHttpService, ValidationTool, ToastrService){

        var form = null;

        $scope.$on('$viewContentLoaded', function(){
            Metronic.initAjax();
            Layout.setSidebarMenuActiveLink("match");
            CommonHttpService.get("/api/supercode/").then(function (exists) {
                $scope.is_init = !exists;
            });
            form = ValidationTool.init('#supercode_submit_form');
        });

        $scope.code = {
            old: null,
            new1: null,
            new2: null
        };

        $scope.has_error = false;

        $scope.submit = function() {
            if(!form.valid()){
                return;
            }
            var post_data = {
                "old": $scope.code.old,
                "new1": $scope.code.new1,
                "new2": $scope.code.new2
            };
            CommonHttpService.post("/api/supercode/", post_data).then(function (data) {
                if (data.success) {
                    ToastrService.success(data.msg, $i18next("success"));
                    $scope.has_error = false;
                } else {
                    ToastrService.error(data.msg, $i18next("op_failed"));
                    $scope.has_error = true;
                }
            });
        };

        $scope.check_can_submit = function() {
            return $scope.code.new1 == $scope.code.new2 && $scope.code.new1 != null;
        };
    });

