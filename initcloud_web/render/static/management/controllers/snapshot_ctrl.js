/**
 * User: arthur 
 * Date: 16-4-17
 **/
CloudApp.controller('SnapshotController',
    function($rootScope, $scope, $filter, $modal, $i18next, $ngBootbox,
             CommonHttpService, ToastrService, ngTableParams, ngTableHelper,
             Snapshot, CheckboxGroup, DataCenter){

        $scope.$on('$viewContentLoaded', function(){
                Metronic.initAjax();
        });

        $scope.snapshots = [];
        var checkboxGroup = $scope.checkboxGroup = CheckboxGroup.init($scope.snapshots);

        $scope.snapshot_table = new ngTableParams({
                page: 1,
                count: 10
            },{
                counts: [],
                getData: function($defer, params){
                    Snapshot.query(function(data){
                        $scope.snapshots = ngTableHelper.paginate(data, $defer, params);
                        checkboxGroup.syncObjects($scope.snapshots);
                    });
                }
            });



        var deleteSnapshots = function(ids){

            $ngBootbox.confirm($i18next("snapshot.confirm_delete")).then(function(){

                if(typeof ids == 'function'){
                    ids = ids();
                }

                CommonHttpService.post("/api/snapshot/batch-delete/", {ids: ids}).then(function(data){
                    if (data.success) {
                        ToastrService.success(data.msg, $i18next("success"));
                        $scope.snapshot_table.reload();
                        checkboxGroup.uncheck()
                    } else {
                        ToastrService.error(data.msg, $i18next("op_failed"));
                    }
                });
            });
        };

        $scope.batchDelete = function(){

            deleteSnapshots(function(){
                var ids = [];

                checkboxGroup.forEachChecked(function(Snapshot){
                    if(snapshot.checked){
                        ids.push(snapshot.id);
                    }
                });

                return ids;
            });
        };

/*         $scope.boot_snap = function(ids){

            $ngBootbox.confirm($i18next("snapshot.boot from snap")).then(function(){

                if(typeof ids == 'function'){
                    ids = ids();
                }

                CommonHttpService.post("/api/snapshot/boot_snapshot/", {ids: ids}).then(function(data){
                    if (data.success) {
                        ToastrService.success(data.msg, $i18next("success"));
                        //$scope.snapshot_table.reload();
                        checkboxGroup.uncheck()
                    } else {
                        ToastrService.error(data.msg, $i18next("op_failed"));
                    }
                });
            });
        };
*/

        $scope.delete = function(snapshot){
            deleteSnapshots([snapshot.id]);
        };


        $scope.edit = function(snapshot){

            $modal.open({
                templateUrl: 'update.html',
                controller: 'SnapshotUpdateController',
                backdrop: "static",
                size: 'lg',
                resolve: {
                    snapshot_table: function () {
                        return $scope.snapshot_table;
                    },
                    snapshot: function(){return snapshot}
                }
            });
        };

        $scope.boot_snapshot = function(snapshot){
            $modal.open({
                templateUrl: 'boot_snapshot.html',
                backdrop: "static",
                controller: 'NewSnapshotController',
                size: 'lg',
                resolve: {
                    snapshot: function(){
                        return snapshot;
                    }
                }
            }).result.then(function(){
                $scope.snapshot_table.reload();
            });
        };
    })


    .controller('NewSnapshotController',
        function($scope, $modalInstance, $i18next, snapshot,
                 CommonHttpService, ToastrService, SnapshotForm){

            var form = null;
            $modalInstance.rendered.then(function(){
                form = SnapshotForm.init();
            });
	    $scope.snapshot = snapshot;
            $scope.instance_name = $scope.snapshot.snapshotname;
            //$scope.snapshot = {is_resource_user: false, is_approver: false};
            $scope.is_submitting = false;
            $scope.cancel = $modalInstance.dismiss;
            $scope.create = function(){
                $scope.is_submitting = true;
                CommonHttpService.post('/api/snapshot/boot_snapshot/', {'id':$scope.snapshot.id,'instance_name':$scope.instance_name}).then(function(result){
                    if(result.success){
                        ToastrService.success(result.msg, $i18next("success"));
                        $modalInstance.close();
                    } else {
                        ToastrService.error(result.msg, $i18next("op_failed"));
                    }
                    $scope.is_submitting = true;
                }).finally(function(){
                    $scope.is_submitting = false;
                });
            };
        }

   ).factory('SnapshotForm', ['ValidationTool', '$i18next',
        function(ValidationTool, $i18next){
            return {
                init: function(){

                    var config = {

                        rules: {
                            snapshotname: {
                                minlength: 2,
                                required: true,
                                remote: {
                                    url: "/api/snapshot/is_snapshotname_unique/",
                                    data: {
                                        snapshotname: $("#snapshotname").val()
                                    },
                                    async: false
                                }
                            },
                            user_type: 'required'
                        },
                        messages: {
                            snapshotname: {
                                remote: $i18next('snapshot.name_is_used')
                            },
                        },
                        errorPlacement: function (error, element) {

                            var name = angular.element(element).attr('name');
                            if(name != 'user_type'){
                                error.insertAfter(element);
                            }
                        }
                    };

                    return ValidationTool.init('#snapshotForm', config);
                }
            }
        }]).controller('SnapshotUpdateController',
        function($rootScope, $scope, $modalInstance, $i18next,
                 snapshot, snapshot_table,
                 Snapshot, UserDataCenter, snapshotForm,
                 CommonHttpService, ToastrService, ResourceTool){

            $scope.snapshot = snapshot = angular.copy(snapshot);

            $modalInstance.rendered.then(snapshotForm.init);

            $scope.cancel = function () {
                $modalInstance.dismiss();
            };


            var form = null;
            $modalInstance.rendered.then(function(){
                form = snapshotForm.init($scope.site_config.WORKFLOW_ENABLED);
            });
            $scope.submit = function(snapshot){

                if(!$("#SnapshotForm").validate().form()){
                    return;
                }

                snapshot = ResourceTool.copy_only_data(snapshot);


                CommonHttpService.post("/api/snapshot/update_snapshot/", snapshot).then(function(data){
                    if (data.success) {
                        ToastrService.success(data.msg, $i18next("success"));
                        snapshot_table.reload();
                        $modalInstance.dismiss();
                    } else {
                        ToastrService.error(data.msg, $i18next("op_failed"));
                    }
                });
            };
        }
   ).factory('snapshotForm', ['ValidationTool', '$i18next',
        function(ValidationTool, $i18next){
            return {
                init: function(){

                    var config = {

                        rules: {
                            snapshotname: {
                                required: true,
                                remote: {
                                    url: "/api/snapshot/is-name-unique/",
                                    data: {
                                        snapshotname: $("#snapshotname").val()
                                    },
                                    async: false
                                }
                            },
                            user_type: 'required'
                        },
                        messages: {
                            snapshotname: {
                                remote: $i18next('snapshot.name_is_used')
                            },
                        },
                        errorPlacement: function (error, element) {

                            var name = angular.element(element).attr('name');
                            if(name != 'user_type'){
                                error.insertAfter(element);
                            }
                        }
                    };

                    return ValidationTool.init('#SnapshotForm', config);
                }
            }
        }]);
