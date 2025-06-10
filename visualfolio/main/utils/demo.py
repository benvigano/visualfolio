import random


def generate_realistic_user():
    first_names = [
        # Western names
        'liam', 'noah', 'oliver', 'elijah', 'william', 'james', 'benjamin', 'lucas', 'henry', 'alexander',
        'michael', 'daniel', 'matthew', 'jackson', 'sebastian', 'david', 'joseph', 'samuel', 'carter', 'wyatt',
        'jayden', 'john', 'owen', 'dylan', 'luke', 'gabriel', 'anthony', 'isaac', 'grayson', 'jack', 'julian',
        'levi', 'christopher', 'joshua', 'andrew', 'lincoln', 'mateo', 'ryan', 'jaxon', 'nathan', 'aaron',
        'isaiah', 'thomas', 'charles', 'caleb', 'josiah', 'christian', 'hunter', 'eli', 'jonathan', 'connor',
        'jeremiah', 'easton', 'adrian', 'asher', 'cameron', 'leo', 'theodore', 'hudson', 'robert', 'ezra',
        'nicholas', 'colton', 'angel', 'jordan', 'dominic', 'austin', 'ian', 'adam', 'elias', 'jaxson',
        'greyson', 'jose', 'ezekiel', 'carson', 'evan', 'maverick', 'bryson', 'jace', 'cooper', 'xavier',
        'zachary', 'parker', 'kayden', 'ayden', 'enzo', 'zayden', 'silas', 'gavin', 'braden', 'sawyer',
        'declan', 'maxwell', 'hayden', 'ryder', 'tristan', 'miles', 'abel',
        'wei', 'ming', 'jun', 'hao', 'yi', 'xiang', 'tao', 'feng', 'gang', 'jie', 'cheng', 'yong', 'hui',
        'xiuying', 'yan', 'ling', 'ping', 'li', 'xia', 'hong', 'lei', 'na', 'zhen', 'yu', 'bin', 'chen',
        'yue', 'hua', 'xin', 'jing', 'yang', 'qiang', 'zhong', 'wen', 'lan', 'fei', 'bo', 'hui', 'xue',
        'akira', 'haruki', 'kenji', 'takeshi', 'yuki', 'satoshi', 'hiroshi', 'kaito', 'riku', 'shota',
        'yuta', 'daiki', 'kenta', 'naoki', 'shinji', 'takashi', 'yusuke', 'kazuki', 'ryota', 'sora',
        'yuki', 'hana', 'yui', 'aoi', 'rin', 'mei', 'mio', 'saki', 'yuna', 'akane', 'haruna', 'misaki',
        'minho', 'jihoon', 'seungho', 'jaewoo', 'hyunwoo', 'jimin', 'taehyung', 'yoongi', 'seokjin',
        'namjoon', 'hoseok', 'jungkook', 'soomin', 'jiyeon', 'hyejin', 'seulgi', 'chaeyoung', 'dahyun',
        'mina', 'sana', 'jihyo', 'nayeon', 'jeongyeon', 'tzuyu', 'yeji', 'ryujin', 'yuna', 'lia',
        'arjun', 'rahul', 'arun', 'vijay', 'rajesh', 'amit', 'suresh', 'deepak', 'ravi', 'ajay',
        'sanjay', 'vikram', 'kumar', 'priya', 'neha', 'pooja', 'anjali', 'divya', 'sneha', 'kavita',
        'meera', 'sunita', 'anita', 'deepika', 'aishwarya', 'ritu', 'geeta', 'sonia', 'madhuri',
        'ahmad', 'mohammed', 'ali', 'hassan', 'hussein', 'omar', 'khalid', 'samir', 'tarek', 'walid',
        'youssef', 'karim', 'nasser', 'ibrahim', 'mustafa', 'fatima', 'aisha', 'layla', 'noor', 'sara',
        'mariam', 'hana', 'zainab', 'leila', 'yasmin', 'rana', 'dalia', 'amira', 'reem', 'salma',
        'ivan', 'dmitri', 'sergei', 'andrei', 'mikhail', 'vladimir', 'alexander', 'nikolai', 'igor',
        'boris', 'pavel', 'oleg', 'yuri', 'anatoly', 'viktor', 'tatiana', 'olga', 'elena', 'natalia',
        'svetlana', 'marina', 'irina', 'anna', 'maria', 'ekaterina', 'sofia', 'daria', 'polina',
        'kwame', 'kofi', 'kwesi', 'kojo', 'kwaku', 'abena', 'adanna', 'chioma', 'folami', 'imani',
        'jabari', 'jelani', 'kenzo', 'mandla', 'olayinka', 'oluwaseun', 'tafari', 'tendai', 'thabo',
        'zola', 'amara', 'ayanna', 'chidera', 'efua', 'eshe', 'folami', 'makena', 'nnamdi', 'olayinka',
        'carlos', 'miguel', 'jorge', 'luis', 'roberto', 'pedro', 'juan', 'francisco', 'diego', 'ricardo',
        'eduardo', 'javier', 'raul', 'fernando', 'alejandro', 'ana', 'maria', 'carmen', 'rosa', 'isabel',
        'patricia', 'sofia', 'valentina', 'gabriela', 'camila', 'lucia', 'daniela', 'andrea', 'paula'
    ]
    
    last_names = [
        'smith', 'johnson', 'williams', 'brown', 'jones', 'garcia', 'miller', 'davis', 'rodriguez',
        'martinez', 'hernandez', 'lopez', 'gonzalez', 'wilson', 'anderson', 'thomas', 'taylor', 'moore',
        'jackson', 'martin', 'lee', 'perez', 'thompson', 'white', 'harris', 'sanchez', 'clark', 'ramirez',
        'lewis', 'robinson', 'walker', 'young', 'allen', 'king', 'wright', 'scott', 'torres', 'nguyen',
        'hill', 'flores', 'green', 'adams', 'nelson', 'baker', 'hall', 'rivera', 'campbell', 'mitchell',
        'carter', 'roberts', 'gomez', 'phillips', 'evans', 'turner', 'diaz', 'parker', 'cruz', 'edwards',
        'collins', 'reyes', 'stewart', 'morris', 'morales', 'murphy', 'cook', 'rogers', 'gutierrez',
        'ortiz', 'morgan', 'cooper', 'peterson', 'bailey', 'reed', 'kelly', 'howard', 'ramos', 'kim',
        'cox', 'ward', 'richardson', 'watson', 'brooks', 'chavez', 'wood', 'james', 'bennett', 'gray',
        'mendoza', 'ruiz', 'hughes', 'price', 'alvarez', 'castillo', 'sanders', 'patel', 'myers', 'long',
        'ross', 'foster', 'jimenez', 'wang', 'li', 'zhang', 'liu', 'chen', 'yang', 'huang', 'zhao', 'wu',
        'zhou', 'xu', 'sun', 'ma',
        'zhu', 'hu', 'guo', 'he', 'gao', 'lin', 'luo', 'zheng', 'liang', 'xie', 'tang', 'xu', 'liu',
        'feng', 'deng', 'cao', 'peng', 'zeng', 'xiao', 'tian', 'dong', 'pan', 'yuan', 'cai', 'jiang',
        'sato', 'suzuki', 'takahashi', 'tanaka', 'watanabe', 'ito', 'yamamoto', 'nakamura', 'kobayashi',
        'kato', 'yoshida', 'yamada', 'sasaki', 'yamaguchi', 'saito', 'matsumoto', 'inoue', 'kimura',
        'hayashi', 'shimizu', 'mori', 'ikeda', 'hashimoto', 'ishikawa', 'yamashita', 'ogawa', 'ishii',
        'kim', 'lee', 'park', 'choi', 'jung', 'kang', 'cho', 'yoon', 'jang', 'lim', 'han', 'yang',
        'hwang', 'shin', 'ahn', 'bae', 'kwon', 'noh', 'seo', 'song', 'hong', 'ryu', 'baek', 'nam',
        'patel', 'sharma', 'singh', 'kumar', 'gupta', 'shah', 'verma', 'joshi', 'pandey', 'mishra',
        'reddy', 'rao', 'nair', 'pillai', 'iyer', 'yadav', 'bhat', 'raj', 'chopra', 'malhotra',
        'kapoor', 'mehta', 'chauhan', 'agarwal', 'sinha', 'trivedi', 'desai', 'patil', 'menon',
        'abdullah', 'ahmed', 'hassan', 'hussein', 'ibrahim', 'khalil', 'mahmoud', 'mohamed', 'rahman',
        'said', 'saleh', 'ali', 'omar', 'ismail', 'malik', 'khan', 'aziz', 'hamid', 'mustafa', 'qureshi',
        'ivanov', 'smirnov', 'kuznetsov', 'popov', 'sokolov', 'lebedev', 'kozlov', 'novikov', 'morozov',
        'petrov', 'volkov', 'solovyov', 'vasiliev', 'zaytsev', 'pavlov', 'semyonov', 'golubev', 'vinogradov',
        'adebayo', 'okafor', 'okonkwo', 'mensah', 'mwangi', 'diallo', 'toure', 'keita', 'afolabi',
        'okoro', 'ndlovu', 'mokoena', 'dube', 'kone', 'traore', 'osei', 'kamara', 'ibrahim', 'nkrumah',
        'silva', 'santos', 'oliveira', 'pereira', 'ferreira', 'rodrigues', 'almeida', 'costa', 'carvalho',
        'gomes', 'martins', 'araujo', 'ribeiro', 'pinto', 'rocha', 'monteiro', 'moraes', 'cavalcanti'
    ]
    
    first_name = random.choice(first_names)
    last_name = random.choice(last_names)
    
    username = f"{first_name}.{last_name}@example.com"
    name = first_name.capitalize() + " " + last_name.capitalize()
    
    return username, name
