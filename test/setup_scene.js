var canvas;
var engine;
var scene;

var createScene = function() {
    // create a basic BJS Scene object
    var scene = new BABYLON.Scene(engine);

    // create a FreeCamera, and set its position to (x:0, y:5, z:-10)
    var camera = new BABYLON.FreeCamera('camera1', new BABYLON.Vector3(0, 5,-10), scene);

    // target the camera to scene origin
    camera.setTarget(BABYLON.Vector3.Zero());

    // attach the camera to the canvas
    camera.attachControl(canvas, false);

    // create a basic light, aiming 0,1,0 - meaning, to the sky
    var light = new BABYLON.HemisphericLight('light1', new BABYLON.Vector3(0,1,0), scene);

    // create a built-in "ground" shape; its constructor takes the same 5 params as the sphere's one
    var ground = BABYLON.Mesh.CreateGround('ground1', 6, 6, 2, scene);

    // return the created scene
    return scene;
}

jQuery(document).ready(function($) {
    canvas = document.getElementById('my_canvas');
    engine = new BABYLON.Engine(canvas, true);
    scene = createScene();
        
    engine.runRenderLoop(function() {
        scene.render();
    });

    window.addEventListener('resize', function() {
        engine.resize();
    });
    
});


function add_mesh(data) {
    BABYLON.SceneLoader.ImportMesh("", "", "data:" + ('{"producer":{"name":"Blender","version":"2.77 (sub 0)","exporter_version":"4.6.1","file":"box.babylon"},\n' +
        '"autoClear":true,"clearColor":[0.0509,0.0509,0.0509],"ambientColor":[0,0,0],"gravity":[0,-9.81,0],\n' +
        '"materials":[{"name":"box.Material","id":"box.Material","ambient":[0.8,0.8,0.8],"diffuse":[0.64,0.64,0.64],"specular":[0.5,0.5,0.5],"emissive":[0,0,0],"specularPower":50,"alpha":1,"backFaceCulling":true,"checkReadyOnlyOnce":false}],\n' +
        '"multiMaterials":[],\n' +
        '"skeletons":[],\n' +
        '"meshes":[{"name":"Cube","id":"Cube","materialId":"box.Material","billboardMode":0,"position":[0,0,0],"rotation":[0,0,0],"scaling":[1,1,1],"isVisible":true,"freezeWorldMatrix":false,"isEnabled":true,"checkCollisions":false,"receiveShadows":false\n' +
        ',"positions":[1,-1,-1,-1,-1,1,1,-1,1,-1,1,1,1,1,-1,1,1,1,-1,-1,-1,-1,1,-1]\n' +
        ',"normals":[0.5773,-0.5773,-0.5773,-0.5773,-0.5773,0.5773,0.5773,-0.5773,0.5773,-0.5773,0.5773,0.5773,0.5773,0.5773,-0.5773,0.5773,0.5773,0.5773,-0.5773,-0.5773,-0.5773,-0.5773,0.5773,-0.5773]\n' +
        ',"indices":[0,1,2,3,4,5,5,0,2,4,6,0,6,3,1,2,3,5,0,6,1,3,7,4,5,4,0,4,7,6,6,7,3,2,1,3]\n' +
        ',"subMeshes":[{"materialIndex":0,"verticesStart":0,"verticesCount":8,"indexStart":0,"indexCount":36}]\n' +
        ',"instances":[]}\n' +
        '],\n' +
        '"cameras":[{"name":"Camera","id":"Camera","position":[7.4811,5.3437,-6.5076],"rotation":[0.4615,-0.8149,0.0108],"fov":0.8576,"minZ":0.1,"maxZ":100,"speed":1,"inertia":0.9,"checkCollisions":false,"applyGravity":false,"ellipsoid":[0.2,0.9,0.2],"cameraRigMode":0,"interaxial_distance":0.0637,"type":"FreeCamera"}],"activeCamera":"Camera",\n' +
        '"lights":[{"name":"Lamp","id":"Lamp","type":0,"position":[4.0762,5.9039,1.0055],"intensity":1,"diffuse":[1,1,1],"specular":[1,1,1]}],\n' +
        '"shadowGenerators":[]\n' +
        '}'), scene, function (meshes) {
    });

}
