"""验证数值教材、变换边界、项目失败分支和本地导航。"""
import contextlib
import io
from html.parser import HTMLParser
from pathlib import Path
import re
import subprocess
import sys
import unittest
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT/'course'))
from lessons import LESSONS
from labs.core import transform, inverse_transform, fuse, project
from labs.slam_1d import estimate, solve, build_system, rmse
from labs.navigation import shortest_path, select_goal, spl, GRAPH, LABELS
from labs.world_model import fit, rollout, plan, mse, TRAIN, TEST


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
        # 伪代码、C++、ROS命令、实验记录不伪装成可执行Python。
        for n,item in enumerate(LESSONS,1):
            if n in (15,16,17,23): continue
            with self.subTest(lesson=n), contextlib.redirect_stdout(io.StringIO()):
                exec(compile(item['code'],f'lesson-{n}','exec'),{})


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
        self.assertEqual(len(LESSONS),23)
        for n,item in enumerate(LESSONS,1):
            self.assertTrue(all(0<p<n for p in item['prereq']))
            for key in ('goal','body','code','trace','question','hint','answer','transfer','refs'):
                self.assertTrue(item[key],f'{n}: {key}')

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
