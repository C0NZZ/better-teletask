from krabbler3 import pingVideoByID
from database2 import getHighestTeletaskID

res200 = []
res404 = []
res401 = []
res403 = []
resError = []

if __name__ == '__main__':
    #highest_id = getHighestTeletaskID()
    #for i in range(highest_id, highest_id + 10):
    for i in range(1,11450):
        res = pingVideoByID(str(i))
        print("response in main")
        print(res + "test")
        if res == "200":
            res200.append(i)
            print(f"Video {i} exists.")
        elif res == "404":
            res404.append(i)
            print(f"Video {i} does not exist.")
        elif res == "401":
            res401.append(i)    
            print(f"Video {i} access denied.")
        elif res == "403":
            res403.append(i)
            print(f"Video {i} forbidden.")
        elif res == "":
            resError.append(i)
            print(f"Video {i} error occurred.")
    
    print("Summary:")
    print(f"200 OK: {len(res200)} videos - IDs: {res200}")
    print(f"404 Not Found: {len(res404)} videos - IDs: {res404}")
    print(f"401 Unauthorized: {len(res401)} videos - IDs: {res401}")
    print(f"403 Forbidden: {len(res403)} videos - IDs: {res403}")
    print(f"Errors: {len(resError)} videos - IDs: {resError}")

    # Save results to file
    with open('output/crawl_results.txt', 'w') as f:
        f.write("Summary:\n")
        f.write(f"200 OK: {len(res200)} videos - IDs: {res200}\n")
        f.write(f"404 Not Found: {len(res404)} videos - IDs: {res404}\n")
        f.write(f"401 Unauthorized: {len(res401)} videos - IDs: {res401}\n")
        f.write(f"403 Forbidden: {len(res403)} videos - IDs: {res403}\n")
        f.write(f"Errors: {len(resError)} videos - IDs: {resError}\n")
