import pickle
import psycopg2
from django.conf import settings
from datetime import datetime
from psycopg2 import OperationalError

class Recommendations:
    def __init__(self):
        
        path_to_artifacts = "./metadata_model/"

        filename1 = path_to_artifacts + "metadata_based_dump.sav"
        with open(filename1 , 'rb') as f1:
            self.model = pickle.load(f1)
        
        filename2 = path_to_artifacts + "metadata_mapping_dump.sav"
        with open(filename2 , 'rb') as f2:
            self.mapping = pickle.load(f2)

        
    def show_recommendations(self, course_id, nrec_items = 6):
        
        course_index = self.mapping[self.mapping['CourseId']==int(course_id)]['CourseIndex']
        
        similarity_score = list(enumerate(self.model[int(course_index)]))
        similarity_score = sorted(similarity_score, key=lambda x: x[1], reverse=True)
    
        # Get the scores of the 15 most similar movies. Ignore the first movie.
        similarity_score = similarity_score[1:nrec_items]
    
        course_indices = [i[0] for i in similarity_score]
        course_list = [[self.mapping[self.mapping['CourseIndex'] == x]['CourseId'].values[0],self.mapping[self.mapping['CourseIndex'] == x]['CourseName'].values[0]]  for x in course_indices]
        
        return course_list
    
    def postprocessing(self, scores):

        try:
            con1 = psycopg2.connect(database=settings.EUSTARD_DATABASE, user=settings.EUSTARD_USER, password=settings.EUSTARD_PASSWORD, host=settings.EUSTARD_HOST, port= settings.EUSTARD_PORT)
            con2 = psycopg2.connect(database=settings.CONTENTQ_DATABASE, user=settings.CONTENTQ_USER, password=settings.CONTENTQ_PASSWORD, host=settings.CONTENTQ_HOST, port= settings.CONTENTQ_PORT)
        except OperationalError as err:
            con1 = None
            con2 = None
            error = str(err)
            status = "Connection failed"
            results = {}

        if con1 != None and con2 != None:    
            cursor1 = con1.cursor()
            cursor2 = con2.cursor()

            query1 = 'SELECT "SubjectId", "SubjectName", "SkillId", "SkillName" FROM public."tblCourseInfo" WHERE "CourseId" = %s'
   
            query2 = '''SELECT "tblProducts"."ProductId", "IsFree", "StandardCost" from public."tblProducts" 
                        INNER JOIN public."tblProductCourses" 
                        ON "tblProducts"."ProductId" = "tblProductCourses"."ProductId"
                        WHERE "tblProductCourses"."CourseId" = %s'''
                
            query3 = '''SELECT AVG("Rating") FROM public."tblCourseRatings"
                        WHERE "tblCourseRatings"."CourseId" = %s
                        GROUP BY "CourseId"'''

            query4 = '''SELECT COUNT("Review") FROM public."tblCourseReviews" 
                        WHERE "tblCourseReviews" ."CourseId" = %s
                        GROUP BY "CourseId"'''
    
            query5 = '''SELECT "OfferId", "OfferValue", "DiscountType" FROM public."tblOffers"
                        WHERE "tblOffers"."ProductId" = %s
                        AND "tblOffers"."ValidFrom" <= %s
                        AND "tblOffers"."ValidTo" >= %s '''
                
            query6 = '''SELECT "PromotionId", "Voucher", "VoucherValue", "DiscountType" FROM public."tblPromotions" 
                        WHERE "ProductId" = %s
                        AND "tblPromotions"."ValidFrom" <= %s
                        AND "tblPromotions"."ValidTo" >= %s '''    
                
            query7 = '''SELECT "fileId", "aboutCourse", "courseDisplayName" FROM public."course"
                        WHERE "course"."id" = %s'''     

            results = {}
            j = 1
            now = datetime.now()          
            try:
                for l in scores:
                    cursor1.execute(query1, (int(l[0]),))
                    row1 = cursor1.fetchone()
                
                    cursor1.execute(query2, (int(l[0]),))
                    row2 = cursor1.fetchone()
                
                    cursor1.execute(query3, (int(l[0]),))
                    row3 = cursor1.fetchone()
                    if row3 is None:
                        rating = 0
                    else:
                        rating = float(row3[0])

                    cursor1.execute(query4, (int(l[0]),))
                    row4 = cursor1.fetchone()
                    if row4 is None:
                        review = 0
                    else:
                        review = int(row4[0])
                        
                    cursor1.execute(query5, (row2[0], now, now))
                    row5 = cursor1.fetchall()
                    if len(row5) == 0:
                        offer = []
                    else:
                        offer = {}
                        i = 1
                        for x in row5:
                            offer[i] = {"OfferId": x[0], "OfferValue": int(x[1]), "DiscountType": x[2]}
                            i = i + 1
                
                    cursor1.execute(query6, (row2[0], now, now))
                    row6 = cursor1.fetchall()
                    if len(row6) == 0:
                        promotion = []
                    else:
                        promotion = {}
                        i = 1
                        for x in row6:
                            promotion[i] = {"PromotionId": x[0], "Voucher": x[1], "VoucherValue": int(x[2]), "DiscountType": x[3]}
                            i = i + 1

                    cursor2.execute(query7, (int(l[0]),))
                    row7 = cursor2.fetchone()
                    if row7 is None:
                        filepath = "null"
                        aboutcourse = "null"
                        displayname = "null"
                    else:
                        if row7[0] is not None:
                            query8 = '''SELECT "FilePath" From public."files" WHERE "files"."id" = %s'''
                            cursor2.execute(query8, (int(row7[0]),))
                            row8 = cursor2.fetchone()
                            filepath = row8[0]
                        else:
                            filepath = "null"
                        aboutcourse = row7[1] if row7[1] is not None else "null"
                        displayname = row7[2] if row7[2] is not None else "null"
                
                    results[j] = {"productId":row2[0], "courseId" : l[0], "courseName":l[1], "subjectId":row1[0], "subjectName": row1[1], 
                            "skillId":row1[2],  "skillName": row1[3], "isFree":row2[1], "standardCost":float(row2[2]), "averageRating":rating, 
                            "reviews":review, "offers":offer, "promotions":promotion, "filePath":filepath, "aboutCourse":aboutcourse, "courseDisplayName":displayname}
                    j = j+1 
            except Exception as err:
                error = str(err)
                status = "Failed Query"
                results = {}

            status = "Success"
            error = 0
            cursor1.close()
            cursor2.close()
            con1.close()
            con2.close()
        return {"data": results, "status": status, "error":error}


    def predict_recommendations(self, course):
        
        course_id = course["course_id"]
        try:
            scores = self.show_recommendations(course_id)
            results = self.postprocessing(scores)
        except Exception as e:
            return {"data":{}, "status": "Failed", "error": str(e)}

        return results

    

   