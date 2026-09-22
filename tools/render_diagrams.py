from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Ellipse, FancyArrowPatch
from matplotlib import font_manager

OUT = Path(__file__).resolve().parents[1] / 'reports' / 'diagrams'
OUT.mkdir(parents=True, exist_ok=True)
font_manager.fontManager.addfont(r'C:\Windows\Fonts\NotoSansSC-VF.ttf')
FONT = 'Noto Sans SC'
plt.rcParams['font.family'] = FONT
plt.rcParams['axes.unicode_minus'] = False

BLUE, LIGHT, GREEN, ORANGE, INK = '#2563eb', '#eff6ff', '#dcfce7', '#fff7ed', '#1e293b'

def setup(title, size=(14, 8)):
    fig, ax = plt.subplots(figsize=size, dpi=180)
    ax.set_xlim(0, 14); ax.set_ylim(0, 8); ax.axis('off')
    ax.text(7, 7.55, title, ha='center', va='center', fontsize=22, weight='bold', color=INK)
    return fig, ax

def box(ax, x, y, w, h, text, fc=LIGHT, ec=BLUE, fs=12, rounded=True):
    p = FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.04,rounding_size=0.12' if rounded else 'square,pad=0.02', fc=fc, ec=ec, lw=1.8)
    ax.add_patch(p); ax.text(x+w/2, y+h/2, text, ha='center', va='center', fontsize=fs, color=INK, wrap=True)
    return (x+w/2, y+h/2)

def arrow(ax, a, b, text=None, rad=0):
    ax.add_patch(FancyArrowPatch(a, b, arrowstyle='->', mutation_scale=15, lw=1.4, color='#64748b', connectionstyle=f'arc3,rad={rad}'))
    if text: ax.text((a[0]+b[0])/2, (a[1]+b[1])/2+0.12, text, ha='center', fontsize=9, color='#475569')

def save(fig, name):
    fig.savefig(OUT / name, bbox_inches='tight', facecolor='white'); plt.close(fig)

def usecase():
    fig, ax = setup('科目一题库系统 UML 用例图')
    box(ax, .5, 3.5, 1.3, .7, '用户', fc=GREEN, ec='#16a34a')
    box(ax, .5, 1.5, 1.3, .7, '管理员', fc=ORANGE, ec='#ea580c')
    items = [('注册 / 登录', 3.0, 5.8), ('章节练习', 5.1, 5.8), ('模拟考试', 7.2, 5.8), ('提交试卷\n查看成绩', 9.3, 5.8), ('查看错题本', 11.4, 5.8), ('使用 Dify\n聊天助手', 3.0, 3.7), ('题目管理', 5.1, 3.7), ('用户管理', 7.2, 3.7), ('题目自动分类', 9.3, 3.7), ('重复题检测\n与审核', 11.4, 3.7)]
    pts = [box(ax, x, y, 1.55, .72, t, fs=10) for t,x,y in items]
    for p in pts[:6]: arrow(ax, (1.8, 3.85), (p[0]-0.8, p[1]))
    for p in pts[6:]: arrow(ax, (1.8, 1.85), (p[0]-0.8, p[1]))
    save(fig, '01_use_case.png')

def sequence():
    fig, ax = setup('提交试卷 UML 时序图')
    names = ['用户', '前端', '考试接口', '试卷服务', '题目表', '记录表']
    xs = [1.1, 3.3, 5.5, 7.7, 9.9, 12.1]
    for x,n in zip(xs,names):
        box(ax,x-.65,6.45,1.3,.55,n,fc=LIGHT,fs=10); ax.plot([x,x],[1.0,6.4], '--', color='#94a3b8', lw=1)
    msgs=[(1,2,'选择试卷并提交答案'),(2,3,'POST 答案'),(3,4,'校验答案'),(4,5,'查询正确答案'),(5,4,'返回标准答案'),(4,4,'计算得分和错题'),(4,5,'保存考试记录'),(5,4,'保存成功'),(4,3,'返回考试结果'),(3,2,'返回成绩'),(2,1,'展示成绩')]
    y=5.8
    for i,j,t in msgs:
        arrow(ax,(xs[i],y),(xs[j],y),t); y-=.43
    save(fig, '02_sequence.png')

def class_diagram():
    fig, ax = setup('科目一题库系统 UML 核心类图', (15, 9))
    nodes=[('User', 'id\nusername\nlogin()', 1,5.5),('Question','id\ncontent\nanswer\ncatId',4,5.5),('QuestionCategory','id\nname',8,5.5),('ExamPaper','id\ntitle',12,5.5),('UserExamRecord','id\nuserId\nscore\nsubmit()',1,2.7),('UserAnswerDetail','id\nrecordId\nquestionId\nuserAnswer\ncorrect',4,2.7),('AiClassification','questionId\ncategory\nconfidence',8,2.7),('QuestionSimilarity','questionId\nsimilarQuestionId\nsimilarity\nmatchType',11.5,2.7)]
    centers={}
    for n,body,x,y in nodes:
        centers[n]=box(ax,x,y,2.5,1.25,n+'\n'+body,fc=LIGHT,fs=9)
    for a,b,t in [('QuestionCategory','Question','分类'),('User','UserExamRecord','参加考试'),('UserExamRecord','UserAnswerDetail','包含答题'),('Question','UserAnswerDetail','被作答'),('Question','AiClassification','AI分类'),('Question','QuestionSimilarity','相似题'),('ExamPaper','Question','试卷题目')]:
        arrow(ax,centers[a],centers[b],t)
    save(fig, '03_class_diagram.png')

def er():
    fig, ax = setup('科目一题库系统数据库 ER 图', (16, 9))
    nodes=[('sys_user','id PK\nusername',.5,5.8),('question_category','id PK\nname',4,5.8),('question','id PK\ncat_id FK\ncontent\nanswer',7.5,5.8),('exam_paper','id PK\ntitle',.5,2.4),('paper_question','paper_id FK\nquestion_id FK',4,2.4),('user_exam_record','id PK\nuser_id FK\nscore',7.5,2.4),('user_answer_detail','id PK\nrecord_id FK\nquestion_id FK',11,2.4),('user_wrong_book','user_id FK\nquestion_id FK',11,5.8),('question_ai_classification','question_id FK\ncategory\nconfidence',4,0.6),('question_similarity','question_id FK\nsimilar_question_id FK\nsimilarity',8,0.6)]
    c={}
    for n,b,x,y in nodes: c[n]=box(ax,x,y,2.5,1.05,n+'\n'+b,fc='#f8fafc',ec='#0f766e',fs=8.5,rounded=False)
    links=[('sys_user','user_exam_record'),('user_exam_record','user_answer_detail'),('question_category','question'),('exam_paper','paper_question'),('question','paper_question'),('question','user_answer_detail'),('sys_user','user_wrong_book'),('question','user_wrong_book'),('question','question_ai_classification'),('question','question_similarity')]
    for a,b in links: arrow(ax,c[a],c[b])
    save(fig, '04_er_diagram.png')

def modules():
    fig, ax = setup('科目一题库系统功能模块图', (14, 8))
    box(ax, 5.2, 5.9, 3.6, .85, '科目一题库系统', fc='#dbeafe', ec=BLUE, fs=16)
    mods=[('用户与权限管理','sys_user / sys_role\nsys_permission / sys_role_perm',.7,3.7,'#dcfce7','#16a34a'),('题库管理','question_category / question',3.7,3.7,'#fef3c7','#ca8a04'),('考试与练习','exam_paper / paper_question\nuser_exam_record',6.7,3.7,'#ede9fe','#7c3aed'),('错题与统计','user_answer_detail\nuser_wrong_book / user_question_stat',9.7,3.7,'#fce7f3','#db2777'),('Dify智能助手','外部 Dify 服务\n无本地业务表',5.2,1.35,'#cffafe','#0891b2')]
    pts=[]
    for t,s,x,y,fc,ec in mods: pts.append(box(ax,x,y,2.5,1.05,t+'\n'+s,fc=fc,ec=ec,fs=10))
    for p in pts: arrow(ax,(7,5.9),(p[0],p[1]+.55))
    save(fig, '05_system_modules.png')

def classification_flow():
    fig, ax = setup('加分项一：题目自动分类算法流程', (16, 9))
    ax.set_xlim(0, 16); ax.set_ylim(0, 9)
    steps=[('题目输入','题干 + 选项 + 图片'),('文本预处理','清理空格、标点\n统一字符'),('关键词弱标注','建立8类初始样本'),('TF-IDF向量化','转换为文本特征向量'),('计算类别中心','每类样本向量求平均'),('余弦相似度','题目向量 vs 各类别中心'),('输出结果','最高分类别 + 置信度\n低置信度人工复核')]
    xs=[.35,2.55,4.75,6.95,9.15,11.35,13.55]
    ps=[]
    for (t,s),x in zip(steps,xs): ps.append(box(ax,x,4.15,1.95,1.45,t+'\n'+s,fc='#eff6ff',ec=BLUE,fs=10))
    for a,b in zip(ps,ps[1:]): arrow(ax,(a[0]+.8,a[1]),(b[0]-.8,b[1]))
    categories = '8类初始样本：\n道路交通安全法律法规｜驾驶证与机动车管理\n道路通行规则｜交通信号与标志标线\n安全文明驾驶常识｜车辆结构与驾驶操作\n紧急情况与事故处理｜其他与综合知识'
    box(ax, 2.3, 1.55, 11.4, 1.65, categories, fc='#fefce8', ec='#ca8a04', fs=11)
    arrow(ax, (5.7, 4.15), (6.0, 3.2), '初始标签')
    ax.text(8,.65,'输出：写入 question_ai_classification，并更新 question.cat_id',ha='center',fontsize=14,color='#334155')
    save(fig, '06_classification_algorithm.png')

def duplicate_flow():
    fig, ax = setup('加分项二：重复题与语义相似题检测流程', (16, 9))
    ax.set_xlim(0, 16); ax.set_ylim(0, 9)
    box(ax,.6,5.6,2.2,.9,'题目集合',fc='#dbeafe',ec=BLUE,fs=13)
    box(ax,3.5,5.6,2.4,.9,'文本规范化',fc='#f8fafc',ec='#64748b',fs=12)
    box(ax,7.0,6.2,2.4,.9,'指纹完全匹配',fc='#dcfce7',ec='#16a34a',fs=12)
    box(ax,7.0,4.5,2.4,.9,'中文语义向量',fc='#ede9fe',ec='#7c3aed',fs=12)
    box(ax,10.4,4.5,2.4,.9,'余弦相似度\n近邻搜索',fc='#ffedd5',ec='#ea580c',fs=12)
    box(ax,10.4,6.2,2.4,.9,'完全重复集合',fc='#dcfce7',ec='#16a34a',fs=12)
    box(ax,10.4,2.7,2.4,.9,'语义相似集合',fc='#fef3c7',ec='#ca8a04',fs=12)
    box(ax,3.5,2.7,2.4,.9,'答案与图片校验',fc='#fce7f3',ec='#db2777',fs=12)
    box(ax,7.0,1.0,2.4,.9,'答案冲突标记\n人工复核',fc='#fee2e2',ec='#dc2626',fs=12)
    arrow(ax,(2.8,6.05),(3.5,6.05)); arrow(ax,(5.9,6.05),(7,6.65)); arrow(ax,(5.9,6.05),(7,4.95)); arrow(ax,(9.4,6.65),(10.4,6.65)); arrow(ax,(9.4,4.95),(10.4,4.95)); arrow(ax,(11.6,4.5),(11.6,3.6)); arrow(ax,(10.4,3.15),(5.9,3.15)); arrow(ax,(6.0,2.95),(7,1.45))
    ax.text(8,.35,'输出：写入 question_similarity，保存相似度、等级和冲突状态',ha='center',fontsize=14,color='#334155')
    save(fig, '07_duplicate_algorithm.png')

if __name__ == '__main__':
    usecase(); sequence(); class_diagram(); er(); modules(); classification_flow(); duplicate_flow(); print(OUT)
