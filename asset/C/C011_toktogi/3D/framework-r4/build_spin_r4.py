"""Bake the two 360-degree turns with alternate planted tripods."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import hashlib
import json
import math
import os
import bpy
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

OUT=Path(__file__).resolve().parent
BASE=Path(bpy.data.filepath).parent
env={"__name__":"flight_export"}
code=bpy.data.texts["EXPORT_PLAYABLE.py"].as_string()
exec(code[:code.index('manifest["source_blend_sha256"]')],env)
rig,visual,skin,scene=(env[k] for k in ("rig","visual","skin","scene"))
manifest=env["manifest"]
runtime=json.loads((BASE/"runtime_poses.json").read_text(encoding="utf8"))
rows=[]
tripods=(('LM','RF','RH'),('LF','LH','RM'))
probe=os.environ.get('TOKTOGI_SPIN_PROBE')=='1'
radius_scale=float(os.environ.get('TOKTOGI_RADIUS','0.86'))
crouch_depth=float(os.environ.get('TOKTOGI_CROUCH','0.035'))


def heading(step):
    return 360 if step>=11 else 0 if step<=0 else 4+35.2*(step-.5)


def body_matrix(f):
    phase=min(11,max(0,int((f-2)/10)))
    u=min(1.,max(0.,(f-2)/10-phase))
    crouch=crouch_depth*min(1.,(f-1)/10,(123-f)/10)
    yaw=4*u if phase==0 else 356+4*u if phase==11 else 4+35.2*(phase-1+u)
    return phase,u,Matrix.Translation((0,0,-crouch))@Matrix.Rotation(math.radians(yaw),4,'Z')


def plan_contacts(neutral):
    points={}
    for phase in range(-1,13):
        rotation=Matrix.Rotation(math.radians(heading(phase)),4,'Z')
        for leg,(ankle,claw,point,_,hip,length) in neutral.items():
            target=rotation@point
            if 1<=phase<=10 and leg in ('RF','RM'):
                neighbor='RM' if leg=='RF' else 'RF'
                away=(point-neutral[neighbor][2]).xy.normalized()
                target.xy+=(rotation.to_3x3()@Vector((*away,0.))).xy*.075
            if 1<=phase<=10:
                target.x*=radius_scale
                target.y*=radius_scale
                limits=[]
                for n in range(41):
                    h=body_matrix(2+phase*10+n*.25)[2]@hip
                    reach=math.sqrt(max(0.,(length-.0015)**2-(h.z-target.z)**2))
                    limits.append((h.xy,reach))
                for _ in range(20):
                    for center,reach in limits:
                        d=target.xy-center
                        if d.length>reach:
                            target.xy=center+d.normalized()*reach
            points[phase,leg]=target
    return points


def bake_feet(phase, u, neutral, plants, heel_blend):
    support=tripods[phase%2]
    for leg,(ankle,claw,point,claw_world,_,_) in neutral.items():
        grounded=leg in support
        progress=u*u*(3-2*u)
        offset=heading(phase) if grounded else heading(phase-1)+(heading(phase+1)-heading(phase-1))*progress
        rotation=Matrix.Rotation(math.radians(offset),4,'Z')
        if grounded:
            target=plants[phase,leg]
        else:
            start=Matrix.Rotation(-math.radians(heading(phase-1)),4,'Z')@plants[phase-1,leg]
            end=Matrix.Rotation(-math.radians(heading(phase+1)),4,'Z')@plants[phase+1,leg]
            target=rotation@start.lerp(end,progress)
            target.z+=.062*math.sin(math.pi*u)**2
        inverse=rig.matrix_world.inverted()
        stem=ankle.name.removesuffix('_Ankle')
        upper,lower=(rig.pose.bones[stem+'_'+part] for part in ('Upper','Lower'))
        # Solve two triangles with the same bend plane and keep the planted claw orientation.
        start=upper.head.copy()
        end=inverse@target
        l1,l2,l3=((b.tail-b.head).length for b in (upper,lower,ankle))
        delta=end-start
        direction=delta.normalized()
        reach=min(l1+l2+l3-1e-6,delta.length)
        shin=max(abs(reach-l1)+1e-6,min(reach+l1-1e-6,(ankle.tail-lower.head).length))
        shin=min(l2+l3-1e-7,max(abs(l2-l3)+1e-7,shin))
        along=(l1*l1-shin*shin+reach*reach)/(2*reach)
        bend=lower.head-start
        bend=(bend-direction*bend.dot(direction)).normalized()
        knee=start+direction*along+bend*math.sqrt(max(0.,l1*l1-along*along))
        end=start+direction*reach
        shin_dir=(end-knee).normalized()
        along=(l2*l2-l3*l3+shin*shin)/(2*shin)
        bend=(ankle.head-lower.head).normalized().lerp(Vector((0,0,1)),heel_blend)
        bend=(bend-shin_dir*bend.dot(shin_dir)).normalized()
        heel_base=knee+shin_dir*along
        heel_offset=bend*math.sqrt(max(0.,l2*l2-along*along))
        heel=heel_base+heel_offset
        for bone,a,b in ((upper,start,knee),(lower,knee,heel),(ankle,heel,end)):
            orient=(bone.tail-bone.head).rotation_difference(b-a)
            matrix=orient.to_matrix().to_4x4()@bone.matrix
            matrix.translation=a
            bone.matrix=matrix
            bpy.context.view_layer.update()
        matrix=inverse@rotation@claw_world
        matrix.translation=claw.head
        claw.matrix=matrix
    bpy.context.view_layer.update()
    return list(support)


def contacts(support):
    evaluated=skin.evaluated_get(bpy.context.evaluated_depsgraph_get())
    units=manifest['coordinate_contract']['world_units_per_pixel']
    return {leg:min((evaluated.matrix_world@evaluated.data.vertices[i].co for i in indices),key=lambda p:p.z)/units
            for leg,indices in manifest['foot_contact_vertex_indices'].items() if leg in support}


def crossing_counts():
    e=skin.evaluated_get(bpy.context.evaluated_depsgraph_get())
    vs=[e.matrix_world@v.co for v in e.data.vertices]
    tree=BVHTree.FromPolygons(vs,triangles,all_triangles=True)
    return sum(a<b and not tri_sets[a]&tri_sets[b] for a,b in tree.overlap(tree))

def fingerprint():
    mesh=skin.data
    value={"vertices":[list(v.co) for v in mesh.vertices],"faces":[list(p.vertices) for p in mesh.polygons],
           "uv":[list(v.uv) for v in mesh.uv_layers.active.data],
           "weights":[[(g.group,g.weight) for g in v.groups] for v in mesh.vertices],
           "bones":[(b.name,b.parent.name if b.parent else None,list(b.head_local),list(b.tail_local)) for b in rig.data.bones],
           "materials":[m.name for m in mesh.materials]}
    return hashlib.sha256(json.dumps(value,sort_keys=True).encode()).hexdigest()

assert fingerprint()==runtime["mesh_uv_weights_rest_hash"]
skin.data.calc_loop_triangles()
triangles=[tuple(t.vertices) for t in skin.data.loop_triangles]
tri_sets=list(map(set,triangles))
archive=OUT/(f"spin_probe_{radius_scale}_{crouch_depth}.zip" if probe else "toktogi_runtime_poses.zip")
with ZipFile(BASE/"toktogi_runtime_poses.zip") as old, ZipFile(archive,"w",ZIP_DEFLATED,compresslevel=4) as packed:
    for name in old.namelist():
        if name!="runtime_poses.json" and not name.startswith('ground_spin_'):packed.writestr(name,old.read(name))
    for view in (('left',) if probe else ('left','right')):
        name="ground_spin_"+view
        poses=[]
        source=target=("idle",view,0)
        original=manifest["clips"][manifest["visual_bindings"]["full_turn"]["ccw"]]
        count=len(original["samples"])
        assert count==62
        supports=[]
        planted={}
        errors=[]
        crosses=[]
        native_frames=[1+i*.25 for i in range(489)]
        plants=None
        for n,f in enumerate(native_frames):
            i=(f-1)/2
            env["set_pose"]("idle",view,manifest["clips"]["idle"]["samples"][0]["frame"])
            if visual.animation_data:visual.animation_data.action=None
            if rig.animation_data:rig.animation_data.action=None
            bpy.context.view_layer.update()
            if 0<i<count-1:
                neutral={}
                for ankle in rig.pose.bones:
                    for constraint in ankle.constraints:
                        if constraint.type=='IK' and constraint.name.startswith('Offline plant '):
                            claw=rig.pose.bones[ankle.name.removesuffix('_Ankle')+'_Claw']
                            w=rig.matrix_world
                            stem=ankle.name.removesuffix('_Ankle')
                            chain=[rig.pose.bones[stem+'_'+part] for part in ('Upper','Lower','Ankle')]
                            length=sum((w.to_3x3()@(bone.tail-bone.head)).length for bone in chain)
                            neutral[constraint.name[-2:]]=(ankle,claw,w@ankle.tail,w@claw.matrix,w@chain[0].head,length)
                assert len(neutral)==6
                if plants is None:plants=plan_contacts(neutral)
                phase,u,transform=body_matrix(f)
                visual.matrix_world=transform@visual.matrix_world
                bpy.context.view_layer.update()
                # Ease out of the idle ankle plane before the first rendered turn cell.
                blend=min(1.,(f-1)/2,(123-f)/2)
                support=bake_feet(phase,u,neutral,plants,blend*blend*(3-2*blend))
                if n%8==0:supports.append(support)
                planar=contacts(support)
                if planar.keys()!=planted.keys():
                    planted=planar
                for leg,p in planar.items():
                    errors.append((abs(p.z),(p.xy-planted[leg].xy).length,f,leg,tuple(p),tuple(planted[leg])))
                if probe and n%8==0:crosses.append((crossing_counts(),f))
            poses.append(([b.matrix_basis.copy() for b in rig.pose.bones],rig.matrix_basis.copy(),visual.matrix_basis.copy()))
        print('PLANT',view,'height',max(errors),'slide',max(errors,key=lambda e:e[1]),flush=True)
        if probe:
            print('OVERLAP',radius_scale,crouch_depth,sum(c[0] for c in crosses),max(crosses),flush=True)
            for leg in sorted(neutral):
                print('FOOT',leg,max(e for e in errors if e[3]==leg),max((e[1],e[2]) for e in errors if e[3]==leg),flush=True)
            continue
        assert max(er[0] for er in errors)<.3 and max(er[1] for er in errors)<1.,view
        actions=[]
        for obj,suffix in ((rig,""),(visual,"_heading")):
            action=bpy.data.actions.new("FW4_"+name+suffix)
            action.use_fake_user=True
            actions.append(action.name)
            obj.animation_data_create()
            obj.animation_data.action=action
            previous_rotation=None
            previous_bones={}
            for i,pose in enumerate(poses):
                for actor in (rig,visual,*rig.pose.bones):actor.rotation_mode="QUATERNION"
                for b,m in zip(rig.pose.bones,pose[0]):b.matrix_basis=m
                rig.matrix_basis=pose[1]
                visual.matrix_basis=pose[2]
                obj.rotation_mode="QUATERNION"
                if previous_rotation is not None and obj.rotation_quaternion.dot(previous_rotation)<0:
                    obj.rotation_quaternion.negate()
                previous_rotation=obj.rotation_quaternion.copy()
                for prop in ("location","rotation_quaternion","scale"):
                    obj.keyframe_insert(data_path=prop,frame=native_frames[i])
                if obj==rig:
                    for bone in rig.pose.bones:
                        bone.rotation_mode="QUATERNION"
                        old=previous_bones.get(bone.name)
                        if old is not None and bone.rotation_quaternion.dot(old)<0:
                            bone.rotation_quaternion.negate()
                        previous_bones[bone.name]=bone.rotation_quaternion.copy()
                        for prop in ("location","rotation_quaternion","scale"):
                            bone.keyframe_insert(data_path=prop,frame=native_frames[i],group=bone.name)
            for layer in action.layers:
                for strip in layer.strips:
                    for bag in strip.channelbags:
                        for fc in bag.fcurves:
                            for key in fc.keyframe_points:key.interpolation="LINEAR"
        cells=[list(source)]
        samples=[]
        for i in range(1,count-1):
            rig.animation_data.action=None
            visual.animation_data.action=None
            for b,m in zip(rig.pose.bones,poses[8*i][0]):b.matrix_basis=m
            rig.matrix_basis=poses[8*i][1]
            visual.matrix_basis=poses[8*i][2]
            bpy.context.view_layer.update()
            env["active_clip"]="idle"
            maps,markers,_,geometry=env["surface_data"](False)
            blob=np.concatenate([maps[p] for p in ("sprite","base","normal","rm","emissive")],axis=0)
            path=OUT/"cell.png"
            env["png"](path,blob)
            packed.writestr(f"{name}/{view}/{i-1}.png",path.read_bytes())
            ys,xs=np.where(maps["sprite"][:,:,3]>0)
            border=int(min(xs.min(),ys.min(),127-xs.max(),127-ys.max()))
            assert border>=2,(name,i,border)
            samples.append({"duration_s":.04,"support":supports[i-1],"work":[],
                            "views":{view:{"markers":markers}},"frame":1+2*i})
            cells.append([name,view,i-1])
            rows.append({"profile":name,"sample":i-1,"frame":1+2*i,"geometry_hash":geometry,"border_px":border})
        cells.append(list(target))
        runtime["clips"][name]={"samples":samples,"supported_views":[view],"loop":False,"duration_s":len(samples)*.04}
        runtime["profiles"][name]={"cells":cells,"durations":[.04]*len(cells),"action":actions[0],"heading_action":actions[1],
            "source":list(source),"target":list(target),"baked_heading":True,"effects":False,"native_fps":50,"native_frame_end":2*count,
            "rotation_axis":"world +Z","rotation_degrees":360,"game_art_direction":True}
        print("SPIN_EXPORTED",name,len(samples),flush=True)
    runtime["revision"]="framework-r4"
    packed.writestr("runtime_poses.json",json.dumps(runtime,ensure_ascii=False,sort_keys=True))

if probe:
    raise SystemExit(0)
assert fingerprint()==runtime["mesh_uv_weights_rest_hash"]
text=bpy.data.texts["RUNTIME_R2_MANIFEST.json"]
text.clear()
text.write(json.dumps(runtime,ensure_ascii=False))
selector=bpy.data.texts["SET_RUNTIME_POSE.py"].as_string()
(OUT/"SET_RUNTIME_POSE.py").write_text(selector,encoding="utf8")
scope={"__name__":"flight_selection"}
exec(selector,scope)
for row in rows:
    scope["select_runtime"](row["profile"],(row["frame"]-1)/50)
    evaluated=skin.evaluated_get(bpy.context.evaluated_depsgraph_get())
    verts=[evaluated.matrix_world@v.co for v in evaluated.data.vertices]
    actual=hashlib.sha256(np.round(np.array(verts),6).tobytes()).hexdigest()
    assert actual==row["geometry_hash"],row
    row["native_action_matches"]=True
scope["select_runtime"]("ground_spin_right",.24)
scene["runtime_profile"]="ground_spin_right"
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/"toktogi_framework_r4.blend"),relative_remap=False)
(OUT/"runtime_poses.json").write_text(json.dumps(runtime,ensure_ascii=False,indent=2),encoding="utf8")
(OUT/"spin_validation.json").write_text(json.dumps({"unchanged_mesh_uv_weights_rest":True,"cells":rows},indent=2),encoding="utf8")
lock={"bundle_sha256":hashlib.sha256(archive.read_bytes()).hexdigest(),"base_signature":runtime["base_signature"],
      "source_blend_sha256":runtime["source_blend_sha256"],
      "runtime_blend_sha256":hashlib.sha256((OUT/"toktogi_framework_r4.blend").read_bytes()).hexdigest(),"revision":"framework-r4"}
(OUT/"toktogi_runtime_poses.source.json").write_text(json.dumps(lock,indent=2),encoding="utf8")
print("FRAMEWORK_NATIVE_READY",len(rows),flush=True)
