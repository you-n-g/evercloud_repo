/**
 * User: arthur 
 * Date: 15-6-29
 * Time: 下午2:11
 **/
CloudApp.controller('ParamsetController',
    function($rootScope, $scope, $filter, $modal, $i18next, $ngBootbox, $window,
             CommonHttpService, ToastrService, ngTableParams, ngTableHelper,
             Paramset, CheckboxGroup){

        $scope.$on('$viewContentLoaded', function(){
                Metronic.initAjax();
        });

        $scope.params = [];
        var checkboxGroup = $scope.checkboxGroup = CheckboxGroup.init($scope.params);

        $scope.param_table = new ngTableParams({
                page: 1,
                count: 10
            },{
                counts: [],
                getData: function($defer, params){
                    CommonHttpService.get('/api/paramset/').then(function(data){
                        $scope.params = ngTableHelper.paginate(data, $defer, params);
                        checkboxGroup.syncObjects($scope.params);
                    });
                }
            });

        $scope.edit = $scope.create = function(param){

            param = param || {};

            $modal.open({
                templateUrl: 'create.html',
                controller: 'ParamsetCreateController',
                backdrop: "static",
                size: 'lg',
                resolve: {
                    param_table: function () {
                        return $scope.param_table;
                    },
                    param: function(){return param}
                }
            });
        };

        var deleteParams = function(keys){

            $ngBootbox.confirm($i18next("paramset.confirm_delete")).then(function(){

                if(typeof keys == 'function'){
                    keys = keys();
                }

                CommonHttpService.post("/api/paramset/batch-delete/", {keys: keys}).then(function(data){
                    if (data.success) {
                        ToastrService.success(data.msg, $i18next("success"));
                        $scope.param_table.reload();
                        checkboxGroup.uncheck()
                        $window.location.reload();
                    } else {
                        ToastrService.error(data.msg, $i18next("op_failed"));
                    }
                });
            });
        };

        $scope.batchDelete = function(){

            deleteParams(function(){
                var keys = [];

                checkboxGroup.forEachChecked(function(param){
                    if(param.checked){
                        keys.push(param.key);
                    }
                });

                return keys;
            });
        };

        $scope.delete = function(param){
            deleteParams([param.key]);
        };
    })
        .controller('ParamsetCreateController',
        function($rootScope, $scope, $modalInstance, $i18next,
                 param, param_table,
                 Paramset, ParamsetForm,
                 CommonHttpService, ToastrService, ResourceTool){

            $scope.param = ResourceTool.copy_only_data(param);

            $modalInstance.rendered.then(ParamsetForm.init);

            $scope.cancel = function () {
                $modalInstance.dismiss();
            };

            $scope.submit = function(param){

                if(!$("#paramsetForm").validate().form()) {
                    return;
                }
                var url = '/api/paramset';

                if(param.key){
                    url += "/update/";
                } else {
                    url += "/create/";
                }
                CommonHttpService.post(url, param).then(function(data){
                    if (data.success) {
                        ToastrService.success(data.msg, $i18next("success"));
                        param_table.reload();
                        $modalInstance.dismiss();
                    } else {
                        ToastrService.error(data.msg, $i18next("op_failed"));
                    }
                });
            };
        }
   )
    .factory('ParamsetForm', ['ValidationTool', '$i18next',
        function(ValidationTool, $i18next){
            return {
                init: function(){
                    var config = {
                        rules: {
                            key: {
                                required: true
                            },
                            value: {
                                required: true
                            }
                        }
                    };
                    return ValidationTool.init('#paramsetForm', config);
                }
            }
        }])
