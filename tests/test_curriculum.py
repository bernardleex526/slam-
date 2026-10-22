"""验证数值教材、变换边界、项目失败分支、本地导航、C++ 示例和部署检查脚本。"""
import contextlib
import io
from html.parser import HTMLParser
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import sys
import unittest
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT/'course'))
from lessons import LESSONS
import build
from labs.core import transform, inverse_transform, fuse, project
from labs.slam_1d import estimate, solve, build_system, rmse
from labs.navigation import shortest_path, select_goal, spl, GRAPH, LABELS
from labs.world_model import fit, rollout, plan, mse, TRAIN, TEST
from labs.deploy import check_bag
KEYS=[item['key'] for item in LESSONS]


class NumericalTests(unittest.TestCase):
    def test_transform_roundtrip(self):
        for angle in (-170, -90, 0, 35, 90, 180):
            for point in ((0.,0.), (1.,2.), (-3.,4.)):
                world = transform(point, (2.,1.), angle)
                recovered = inverse_transform(world,(2.,1.),angle)
                for a,b in zip(point,recovered): self.assertAlmostEqual(a,b)

    def test_rotation_preserves_distance(self):
        for angle in (0,35,90):
            x,y=transform((3.,4.),(0.,0.),angle)
            self.assertAlmostEqual(x*x+y*y,25.)

    def test_fusion_numbers_and_confidence(self):
        x,p,k=fuse(0,.04,1,.01,1.2,.2)
        self.assertAlmostEqual(x,1.04); self.assertAlmostEqual(p,.04); self.assertAlmostEqual(k,.2)
        self.assertAlmostEqual(fuse(0,.04,1,.01,1.2,.05)[0],1.1)
        with self.assertRaises(ValueError): fuse(0,-1,1,0,2,1)
        with self.assertRaises(ValueError): fuse(0,0,1,0,2,0)

    def test_camera_scale_and_invalid_depth(self):
        self.assertEqual(project((1,.5,2)),(520.,340.))
        self.assertEqual(project((2,1,4)),(520.,340.))
        self.assertEqual(project((1,.5,4)),(420.,290.))
        with self.assertRaises(ValueError): project((1,1,0))
        with self.assertRaises(ValueError): project((1,1,-1))

    def test_slam_solution_and_stationary_objective(self):
        positions,m=estimate()
        for x,expected in zip(positions,[0,1.1375,2.05]): self.assertAlmostEqual(x,expected)
        self.assertAlmostEqual(m,4.0625)
        a,b=build_system(); y=positions[1:]+[m]
        residual=[sum(v*w for v,w in zip(row,y))-z for row,z in zip(a,b)]
        for j in range(3): self.assertAlmostEqual(sum(row[j]*r for row,r in zip(a,residual)),0)
        self.assertAlmostEqual(rmse(positions,[0,1,2]),0.08447139555297206,places=7)

    def test_slam_landmark_shift_and_exact_data(self):
        p,m=estimate(observations=(6,5,4)); p0,m0=estimate()
        for a,b in zip(p,p0): self.assertAlmostEqual(a,b)
        self.assertAlmostEqual(m,m0+2)
        p,m=estimate((1,1),(4,3,2))
        for a,b in zip(p,[0,1,2]): self.assertAlmostEqual(a,b)
        self.assertAlmostEqual(m,4)

    def test_underconstrained_system(self):
        with self.assertRaises(ValueError): solve([[1,-1],[-1,1]],[1,-1])

    def test_navigation_success_missing_and_ambiguous(self):
        self.assertEqual(shortest_path(GRAPH,'S',select_goal(LABELS,'red door')),['S','A','R'])
        self.assertEqual(shortest_path(GRAPH,'S','S'),['S'])
        self.assertIsNone(shortest_path({'S':[],'R':[]},'S','R'))
        with self.assertRaises(ValueError): select_goal(LABELS,'green door')
        with self.assertRaises(ValueError): select_goal({'A':'red','B':'red'},'red')
        self.assertEqual(spl(False,4,4),0)
        self.assertAlmostEqual(spl(True,4,6),2/3)

    def test_world_model_holdout_and_shift(self):
        theta=fit(TRAIN)
        self.assertAlmostEqual(theta,.799)
        self.assertLess(mse(theta,TEST),mse(1,TEST))
        actions=plan(0,1.6,theta)
        self.assertEqual(actions,(1.,1.))
        self.assertAlmostEqual(rollout(0,actions,theta)[-1],1.598)
        self.assertAlmostEqual(rollout(0,actions,.5)[-1],1.)
        with self.assertRaises(ValueError): fit([(0,0)])

    def test_python_lesson_examples_execute(self):
        # 只执行标记为可运行的 Python；C++、终端命令、伪代码和实验记录不伪装成可执行 Python。
        for n,item in enumerate(LESSONS,1):
            if not (item['runnable'] and item['lang']=='python'): continue
            with self.subTest(lesson=item['key']), contextlib.redirect_stdout(io.StringIO()):
                exec(compile(item['code'],f'lesson-{n}','exec'),{'__name__':'__lesson__'})

    def test_split_lessons_state_correct_numbers(self):
        # 旧第 7 课曾把一步梯度下降后的分数写成 3.28，正确值是 2.72。
        out=io.StringIO()
        with contextlib.redirect_stdout(out): exec(LESSONS[KEYS.index('lsq_iterate')]['code'],{})
        self.assertEqual(out.getvalue().split('\n')[0].split(),['1','5.4','2.72'])
        out=io.StringIO()
        with contextlib.redirect_stdout(out): exec(LESSONS[KEYS.index('pose_chain')]['code'],{})
        self.assertIn('[2.0, 2.2]',out.getvalue())


class DeployCheckTests(unittest.TestCase):
    info=(ROOT/'labs/deploy/sample_rosbag_info.txt').read_text(encoding='utf-8')
    config=(ROOT/'labs/deploy/sample_config.yaml').read_text(encoding='utf-8')

    def test_sample_reports_wrong_imu_topic(self):
        problems,notes=check_bag.check(self.info,self.config)
        self.assertEqual(len(problems),1); self.assertIn('imu_topic',problems[0])
        self.assertTrue(any('10 Hz' in n for n in notes))

    def test_fixed_config_passes(self):
        problems,notes=check_bag.check(self.info,self.config.replace('/imu/data','/livox/imu'))
        self.assertEqual(problems,[])
        self.assertTrue(any('200 Hz' in n for n in notes))

    def test_pointcloud2_with_livox_type_is_rejected(self):
        info=self.info.replace('livox_ros_driver/CustomMsg','sensor_msgs/PointCloud2')
        problems,_=check_bag.check(info,self.config.replace('/imu/data','/livox/imu'))
        self.assertTrue(any('lidar_type' in p for p in problems))

    def test_script_exit_code(self):
        result=subprocess.run([sys.executable,str(ROOT/'labs/deploy/check_bag.py')],capture_output=True,text=True)
        self.assertEqual(result.returncode,1); self.assertIn('问题',result.stdout)

    def test_shell_scripts_syntax(self):
        if not shutil.which('bash'): self.skipTest('no bash')
        for name in ('run.sh','build_fastlio.sh'):
            result=subprocess.run(['bash','-n',str(ROOT/'labs/deploy'/name)],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)


class CppTests(unittest.TestCase):
    FILES={'cpp_basics':'labs/cpp/01_basics.cpp','cpp_functions':'labs/cpp/02_functions.cpp','cpp_eigen_cmake':'labs/cpp/eigen_demo/main.cpp'}

    def test_repo_files_match_lesson_code(self):
        for key,path in self.FILES.items():
            code=build.resolve(LESSONS[KEYS.index(key)]['code'],html=False)
            self.assertEqual((ROOT/path).read_text(encoding='utf-8').strip(),code.strip(),path)

    def test_plain_cpp_compiles_and_runs(self):
        if not shutil.which('g++'): self.skipTest('no g++')
        expected={'labs/cpp/01_basics.cpp':'3 3.5','labs/cpp/02_functions.cpp':'3.2'}
        with tempfile.TemporaryDirectory() as tmp:
            for path,needle in expected.items():
                exe=str(Path(tmp)/'a.out')
                build=subprocess.run(['g++','-std=c++17','-Wall','-Werror',str(ROOT/path),'-o',exe],capture_output=True,text=True)
                self.assertEqual(build.returncode,0,build.stderr)
                self.assertIn(needle,subprocess.run([exe],capture_output=True,text=True).stdout)

    def test_eigen_demo_compiles_when_eigen_available(self):
        include=next((p for p in ('/usr/include/eigen3','/usr/local/include/eigen3','/tmp/eig/include/eigen3') if Path(p,'Eigen').exists()),None)
        if not (shutil.which('g++') and include): self.skipTest('no Eigen')
        with tempfile.TemporaryDirectory() as tmp:
            exe=str(Path(tmp)/'demo')
            build=subprocess.run(['g++','-std=c++17','-I',include,str(ROOT/'labs/cpp/eigen_demo/main.cpp'),'-o',exe],capture_output=True,text=True)
            self.assertEqual(build.returncode,0,build.stderr)
            self.assertIn('2 2',subprocess.run([exe],capture_output=True,text=True).stdout)


class Links(HTMLParser):
    def __init__(self):
        super().__init__(); self.targets=[]; self.ids=[]
    def handle_starttag(self,tag,attrs):
        values=dict(attrs)
        if 'id' in values:self.ids.append(values['id'])
        if tag in ('a','link','script','img'):
            value=values.get('href') or values.get('src')
            if value:self.targets.append(value)


class ArtifactTests(unittest.TestCase):
    def test_local_file_links_and_new_page_anchors(self):
        for file in ROOT.rglob('*.html'):
            if '.git' in file.parts: continue
            parser=Links(); parser.feed(file.read_text(encoding='utf-8'))
            is_new=file.parent.name in ('lessons','reference') or file.name=='index.html'
            if is_new:self.assertEqual(len(parser.ids),len(set(parser.ids)),str(file))
            for target in parser.targets:
                url=urlsplit(target)
                if url.scheme or url.netloc:continue
                path=(file.parent/unquote(url.path)).resolve() if url.path else file
                self.assertTrue(path.exists(),f'{file.name}: missing {target}')
                if is_new and url.fragment and path.suffix=='.html':
                    dest=Links();dest.feed(path.read_text(encoding='utf-8'))
                    self.assertIn(unquote(url.fragment),dest.ids,f'{file.name}: missing anchor {target}')

    def test_prerequisites_are_previous_lessons(self):
        self.assertEqual(len(LESSONS),33)
        self.assertEqual(len(KEYS),len(set(KEYS)))
        for n,item in enumerate(LESSONS,1):
            self.assertTrue(all(p in KEYS[:n-1] for p in item['prereq']),item['key'])
            for key in ('goal','body','code','trace','question','hint','answer','transfer','refs','analogy','summary','time','check'):
                self.assertTrue(item[key],f'{n}: {key}')

    def test_lesson_pages_have_ai_coach_and_no_placeholders(self):
        for n in range(1,len(LESSONS)+1):
            text=(ROOT/'lessons'/f'{n:04d}-lesson.html').read_text(encoding='utf-8')
            self.assertIn('id="ai"',text,n); self.assertIn('data-copy',text,n); self.assertIn('一句话总结',text,n)
            self.assertNotIn('{L:',text,n)
        self.assertTrue((ROOT/'reference/ai.html').exists())

    def test_new_terms_per_lesson_are_limited(self):
        source=(ROOT/'course/build.py').read_text(encoding='utf-8')
        keys=re.findall(r"^ \('[^']*','[^']*','(\w+)'\),?$",source,re.M)
        self.assertTrue(keys)
        for key in set(keys):
            self.assertIn(key,KEYS); self.assertLessEqual(keys.count(key),6,key)

    def test_legacy_pages_warn_about_scope_and_ros_version(self):
        for file in ROOT.glob('第*周学习教材.html'):
            text=file.read_text(encoding='utf-8')
            if '原仓库没有第五周文件' not in text: self.assertIn('zero-foundation-entry',text,file.name)
            self.assertNotIn('零基础自包含版',text,file.name)
            body=re.sub(r'<aside id="ros-version-warning".*?</aside>','',text,flags=re.S).lower()
            if any(w in body for w in ('ros2','ros 2','jazzy','fast-lio','fast_lio')):
                self.assertIn('ros-version-warning',text,file.name)

    def test_generated_javascript_syntax(self):
        result=subprocess.run(['node','--check',str(ROOT/'assets/app.js')],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)

    def test_cross_page_learning_records(self):
        result=subprocess.run(['node',str(ROOT/'tests/storage.test.js')],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)

    def test_legacy_css_fixed(self):
        for file in ROOT.glob('第*周学习教材.html'):
            text=file.read_text(encoding='utf-8')
            for body in re.findall(r'<style>(.*?)</style>',text,re.S):
                self.assertNotIn('{{',body,str(file))


if __name__=='__main__': unittest.main()
