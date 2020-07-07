from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql
import mysql.connector

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False
CORS(app)

@app.route('/')
def index():
    return "collegecounsel api by Jiaqi Wang"


@app.route('/getData')
def getAllData():
    args = request.args
    con = mysql.connector.connect(user='admin', password='Jiaqi200218',
                                  host='collegedata.cwfud0qzqwsy.us-east-2.rds.amazonaws.com',
                                  database='collegeStats')
    cursor = con.cursor()
    alldata = dict()
    if args:
        if "sort" in args:
            if args["sort"] == "alpha":
                print("here1")
                sql = "select * from data ORDER BY SchoolName"
            elif args["sort"] == "admitasc":
                print("here2")
                sql = "select * from data ORDER BY PercentAdmitted"
            elif args["sort"] == "admitdes":
                sql = "select * from data ORDER BY PercentAdmitted DESC"
                print("here3")
            cursor.execute(sql)
            data = cursor.fetchall()
            con.close()
        elif "schoolname" in args:
            name = str(args["schoolname"])
            sql = "select * from data WHERE SchoolName = %s"
            cursor.execute(sql,(name,))
            data = cursor.fetchall()
            con.close()
            print(data)
            #return jsonify(data)
    else:
        sql = "SELECT * FROM data"
        cursor.execute(sql)
        data = cursor.fetchall()
        con.close()

    for schoolData in data:
        alldata[schoolData[1]]= \
            { 'name':schoolData[1],
                'acceptance rate': schoolData[2],
                'total admitted': schoolData[3],
                'Interview': schoolData[4],
                "gpa(uw) 75th percentile": schoolData[5],
                "gpa(uw) 25th percentile": schoolData[6],
                'SAT 75th percentile': schoolData[9],
                'SAT 25th percenile': schoolData[10],
                'ACT 75th percentile': schoolData[11],
                'ACT 25th percentile': schoolData[12],
                'estimated total enrollment': schoolData[13],
                'estimated total undergrad enrollment': schoolData[14],
                'admission yield': str(round(schoolData[15])) + "%",
                'average cost of attendance per year': schoolData[16],
                'out of state cost of attendance per year': schoolData[17],
                'location': schoolData[18],
                'graduation rate': str(round(schoolData[19])) + "%",
                'strong majors': schoolData[20].split("breaker"),
                'admissions stats':schoolData[21],
                'admissions req': schoolData[22],
                'test optional':schoolData[23]
            }

    return jsonify(alldata)

@app.route('/build')
def buildList():
    #https://collegedatasender.herokuapp.com/build?sat=1500&gpa=3.9&number=20&state=CA
    args = request.args
    gpa=float(args["gpa"])
    if 'sat' in args:
        testscore=int(args["sat"])
        ifsat = True
    else:
        testscore=int(args["act"])
        ifsat=False

    numberOfSchools=int(args["number"])
    if 'maxcost' in args:
        maxCostBeforeAid=int(args["maxcost"])
    else:
        maxCostBeforeAid=99999999

    if('major' in args):
        desiredMajor=args['major']
        major = True
    else:
        major = False
    states=[]
    if('state' in args):
        states= args['state'].split('and')
        stateparm= True
    else:
        stateparm=False
    numberOfReach=round(0.3*numberOfSchools)
    numberOfMatch=round(0.5*numberOfSchools)
    numerOfSafety=round(0.3*numberOfSchools)

    con = mysql.connector.connect(user='admin', password='Jiaqi200218',
                                  host='collegedata.cwfud0qzqwsy.us-east-2.rds.amazonaws.com',
                                  database='collegeStats')
    cursor = con.cursor()
    cursor.execute("SELECT * FROM data")
    data = cursor.fetchall()
    con.close()
    alldata = dict()
    for schoolData in data:
        loc =  schoolData[18].split(",")[1]
        print(loc)
        add=False
        for state in states:
            print(state+":"+loc)
            if state in loc:
                add=True
                break
        if add or not stateparm:
            print('adding')
            alldata[schoolData[1]] = \
                {'name': schoolData[1],
                 "gpa75": schoolData[5],
                 "gpa25": schoolData[6],
                 'sat75': schoolData[9],
                 'sat25': schoolData[10],
                 'act75': schoolData[11],
                 'act25': schoolData[12],
                 'cost': schoolData[16],
                 'strong majors': schoolData[20].split("breaker")
                 }


    reaches=[]
    safeties=[]
    macthes=[]

    for schoolname in alldata:
        gpa75=alldata[schoolname]['gpa75']
        gpa25=alldata[schoolname]['gpa25']
        sat75 = alldata[schoolname]['sat75']
        sat25 = alldata[schoolname]['sat25']
        meansat=(sat75+sat25)/2
        act75 = alldata[schoolname]['act75']
        act25 = alldata[schoolname]['act25']
        meanact=round((act75+act25)/2)
        cost = alldata[schoolname]['cost']
        #strongmajors=alldata[schoolname]['strong majors']
        if cost > maxCostBeforeAid:
            continue
        if ifsat:

            if testscore > 1500:
                testscore = 1500
            if gpa > gpa75:
                if testscore >= sat75:
                    safeties.append(schoolname)
                elif testscore <= meansat:
                    reaches.append(schoolname)
                else:
                    macthes.append(schoolname)
            elif gpa < gpa25:
                if testscore >= sat75:
                    macthes.append(schoolname)
                else:
                    reaches.append(schoolname)
            else:
                if testscore<= meansat:
                    reaches.append(schoolname)
                else:
                    macthes.append(schoolname)
        else:
            if gpa > gpa75:
                if testscore > act75:
                    safeties.append(schoolname)
                elif testscore < meanact:
                    reaches.append(schoolname)
                else:
                    macthes.append(schoolname)
            elif gpa < gpa25:
                if testscore > act75:
                    macthes.append(schoolname)
                else:
                    reaches.append(schoolname)
            else:
                if testscore <= meanact:
                    reaches.append(schoolname)
                else:
                    macthes.append(schoolname)

    totalReach = min(len(reaches),numberOfReach)
    totalMatch=min(len(macthes),numberOfMatch)
    totalSafty=min(len(macthes),numerOfSafety)
    print(reaches)
    print(macthes)
    print(safeties)
    majoredReach = []
    majoredMatch = []
    majoredSafety=[]
    if major:
        desiredMajor = desiredMajor.split(" ")[0]
        counter = 0
        for school in reaches:
            if counter >= totalReach:
                break
            strongmajors = alldata[school]['strong majors']
            for major in strongmajors:
                if desiredMajor in major or major in desiredMajor:
                    majoredReach.append(school)
                    reaches.pop(reaches.index(school))
                    counter+=1
                    break

        counter = 0
        for school in macthes:
            if counter >= totalMatch:
                break
            strongmajors = alldata[school]['strong majors']
            for major in strongmajors:
                if desiredMajor in major or major in desiredMajor:
                    majoredMatch.append(school)
                    macthes.pop(macthes.index(school))
                    counter += 1
                    break

        counter = 0
        for school in safeties:
            if counter >= totalSafty:
                break
            strongmajors = alldata[school]['strong majors']
            for major in strongmajors:
                if desiredMajor in major or major in desiredMajor:
                    majoredSafety.append(school)
                    safeties.pop(safeties.index(school))
                    counter += 1
                    break

    print(majoredReach)
    print(majoredMatch)
    print(majoredSafety)

    if len(majoredReach)<numberOfReach:
        try:
            for i in range(numberOfReach-len(majoredReach)):
                majoredReach.append(reaches[i])
        except:
            None
    elif len(majoredReach)>numberOfReach:
        majoredReach=majoredReach[0:numberOfReach]

    if len(majoredMatch)<numberOfMatch:
        try:
            for i in range(numberOfMatch-len(majoredMatch)):
                majoredMatch.append(macthes[i])
        except:
            None
    elif len(majoredMatch)>numberOfMatch:
        majoredMatch=majoredMatch[0:numberOfMatch]

    if len(majoredSafety)<numerOfSafety:
        try:
            for i in range(numerOfSafety-len(majoredSafety)):
                majoredSafety.append(safeties[i])
        except:
            None
    elif len(majoredSafety)>numerOfSafety:
        majoredSafety=majoredSafety[0:numerOfSafety]

    print(majoredReach)
    print(majoredMatch)
    print(majoredSafety)
    out = dict()

    out["Reach"]=majoredReach
    out["Match"]=majoredMatch
    out["Safety"]=majoredSafety

    print(len(majoredSafety)+len(majoredMatch)+len(majoredReach))

    return jsonify(out)


