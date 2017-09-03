from truthfinder import *

# worker selection probability is different from the truthfinder similation
#start assignment
    # calculate_dei(confidence of answer/expertise)
    # assign_with_mode
    #generate and store answers
    #normalization
#end assignment

#to do:
# 1. check completed tasks (pre-scan, stop assign them to workers)
# 2. cold start workers/tasks, old workers/tasks: last batch paras, new workers/tasks: initialized
# 3. consider task processing time, construct a available worker set
# 4. check workers that have done all tasks(can be implemented with 3)
# 5. normalization of confidence
# 6. try different prescan
# 7. adjust paras
# 8. worker select probs(use inferred expertise&difficulty to calculate dei and use truth&difficulty to simulate worker selection prob!!)


def init(num_of_workers, expertise_init, num_of_tasks, difficulty_init):
    return initialization(num_of_workers, expertise_init, num_of_tasks, difficulty_init)


def check_assignment(worker, task, assign_scheme_tbw):
    if assign_scheme_tbw[0][task][worker] is 1 or assign_scheme_tbw[1][task][worker] is 1:
        return True
    else:
        return False


def full_assign(worker, num_of_tasks, assign_scheme_tbw,completed_tasks):
    assigned_task = completed_tasks
    num_of_assign = len(assigned_task)
    for i in range(num_of_tasks):
        if i not in assigned_task and check_assignment(worker, i, assign_scheme_tbw) is True:
            assigned_task.append(i)
            num_of_assign += 1
    if num_of_assign == num_of_tasks:
        return [True, assigned_task]
    else:
        return [False, assigned_task]


def generate_random_task(num_of_tasks, completed_tasks, assigned_tasks):
    worker_ban_task_list = completed_tasks + assigned_tasks
    return np.random.choice([i for i in range(0, num_of_tasks) if i not in worker_ban_task_list])


def select_task(worker, num_of_tasks, assign_scheme_tbw, completed_tasks):
    [full, assigned_tasks] = full_assign(worker, num_of_tasks, assign_scheme_tbw,completed_tasks)
    if full is True:
        return -1
    else:
        task = generate_random_task(num_of_tasks, completed_tasks, assigned_tasks)
        return task


def generate_answer(worker, task, num_of_choices, truths, expertise_truths, difficulty_truths): # check normalization is needed? # add truths as paras
    # 1. not related to truths
    #     if uniform_random_generator(0,1) < prob_ans_wbt[0][worker][task]:
    #         return 0
    #     else:
    #         return 1
    #2. related to truths
    # prob = 1/(1 + np.power(math.e, -3 * expertise_truths[worker] * difficulty_truths[task])) 3 is too high for random above 0.8
    prob = 1 / (1 + np.power(math.e, -expertise_truths[worker] * difficulty_truths[task]))
    return int(choices_generator(prob, num_of_choices, truths[task])) - 1


def random_assign(num_of_workers, num_of_tasks, num_of_choices, assign_scheme_tbw, completed_tasks, truths, expertise_truths, difficulty_truths): #available worker set
    for i in range(num_of_workers):
        task = select_task(i, num_of_tasks, assign_scheme_tbw, completed_tasks)
        print "assign worker ", i, " task ", task
        if task is not -1:
            choice = generate_answer(i, task, num_of_choices, truths, expertise_truths, difficulty_truths) # check whether assignment_scheme_tbw is updated
            assign_scheme_tbw[choice][task][i] = 1
        else:
            #this worker has completed all avialable tasks, do not assign any task
            pass


def prescan(num_of_workers, num_of_tasks, num_of_choices, task_capacity, dei_wbt, assign_scheme_tbw, completed_tasks, truths, expertise_truths, difficulty_truths): # label completed tasks
    # a question is assigned if all workers can complete it: ok(largest negative remaining capacity over workers)
    # a question is assigned if there is a worker who can complete it
    remain_capacity_wbt = np.subtract(task_capacity, dei_wbt)
    available_workers = range(num_of_workers)
    for i in range(num_of_tasks):
        if i not in completed_tasks:
            min = 1000
            min_worker = -1
            for j in available_workers:
                current = remain_capacity_wbt[j][i]
                if current <= 0:
                    if min > 0 or (min < 0 and min < current): #have to check
                        min = current
                        min_worker = j
            if min <= 0:        #assign task i to min_worker
                choice = generate_answer(min_worker, i, num_of_choices, truths, expertise_truths, difficulty_truths)
                assign_scheme_tbw[choice][i][min_worker] = 1
                available_workers.remove(min_worker)
                completed_tasks.append(i)
                print "prescan assign worker ", min_worker, " task ", i
    return available_workers


def assign_first_open(num_of_workers, num_of_tasks, num_of_choices, dei_wbt, remain_capacity_wbt, assign_scheme_tbw, completed_tasks, available_workers, open_tasks, truths, expertise_truths, difficulty_truths):
    #to do: can not find first open
    min_task = ""
    min_worker = ""
    min_dei = 10000
    for w in range(num_of_workers):
        for t in range(num_of_tasks):
            current = remain_capacity_wbt[w][t]
            if w in available_workers and t not in completed_tasks and current < min_dei:
                min_dei = current
                min_worker = w
                min_task = t

    print "assign first worker ", min_worker, " task ", min_task

    process_assignment(min_worker, min_task, num_of_choices, assign_scheme_tbw, available_workers,dei_wbt,remain_capacity_wbt,truths, expertise_truths, difficulty_truths)
    open_tasks.append(min_task)


def update_dei(worker, task, reduced_dei, remain_capacity_wbt):
    remain_capacity_wbt[:,task] = remain_capacity_wbt[:,task] - [reduced_dei] #have to check
    remain_capacity_wbt[worker, task] += reduced_dei


def process_assignment(worker, task, num_of_choices, assign_scheme_tbw, available_workers, dei_wbt, remain_capacity_wbt, truths, expertise_truths, difficulty_truths):
    choice = generate_answer(worker, task, num_of_choices, truths, expertise_truths, difficulty_truths)
    assign_scheme_tbw[choice][task][worker] = 1
    available_workers.remove(worker)
    update_dei(worker, task, dei_wbt[worker][task], remain_capacity_wbt)
    print "process assign worker ", worker, " task ", task


def assign_to_first_open(worker, dei_wbt, open_tasks, assign_scheme_tbw, available_workers,remain_capacity_wbt, num_of_choices, truths, expertise_truths, difficulty_truths):
    for task in open_tasks:
        if dei_wbt[worker][task] >= 0:
            process_assignment(worker, task, num_of_choices, assign_scheme_tbw, available_workers, dei_wbt, remain_capacity_wbt, truths, expertise_truths, difficulty_truths)
            return True
    return False


def assign_to_closed(worker, num_of_tasks, dei_wbt, remain_capacity_wbt, assign_scheme_tbw, completed_tasks, available_workers, open_tasks, num_of_choices,truths, expertise_truths, difficulty_truths):
    min_task = ""
    min_dei = 10000
    for task in range(num_of_tasks):
        current = remain_capacity_wbt[worker][task]
        if task not in completed_tasks and 0 <= current < min_dei:
            min_task = task
            min_dei = current
    print "assign to closed "
    process_assignment(worker, min_task, num_of_choices, assign_scheme_tbw, available_workers, dei_wbt, remain_capacity_wbt, truths, expertise_truths, difficulty_truths)
    open_tasks.append(min_task)


def start_first_fit(num_of_workers, num_of_tasks, num_of_choices, task_capacity, dei_wbt, assign_scheme_tbw, completed_tasks, available_workers, truths, expertise_truths, difficulty_truths):
    remain_capacity_wbt = np.subtract(task_capacity, dei_wbt) # after prescan, available_worker have "positive" dei over all non-completed tasks
    open_tasks = []
    assign_first_open(num_of_workers, num_of_tasks, num_of_choices, dei_wbt, remain_capacity_wbt, assign_scheme_tbw, completed_tasks, available_workers, open_tasks, truths, expertise_truths, difficulty_truths)
    for worker in available_workers:
        if assign_to_first_open(worker, dei_wbt, open_tasks, assign_scheme_tbw, available_workers,remain_capacity_wbt,num_of_choices, truths, expertise_truths, difficulty_truths) is False:
            # 1. open next open
            # 2. no tasks suitable (haven't considered, #open task = #tasks, may assign with smallest exceeding capacity )
            if len(open_tasks) < num_of_tasks:
                assign_to_closed(worker, num_of_tasks, dei_wbt, remain_capacity_wbt, assign_scheme_tbw,completed_tasks, available_workers, open_tasks, num_of_choices, truths, expertise_truths,difficulty_truths)
            else:
                # pass #2. no tasks suitable (haven't considered, #open task = #tasks, may assign with smallest exceeding capacity )
                # assign_to_random_open
                process_assignment(worker, open_tasks[0], num_of_choices, assign_scheme_tbw, available_workers, dei_wbt, remain_capacity_wbt,truths, expertise_truths, difficulty_truths)


def first_fit_greedy(num_of_workers, num_of_tasks, num_of_choices, task_capacity, dei_wbt, assign_scheme_tbw, completed_tasks, truths, expertise_truths, difficulty_truths):
    available_workers = prescan(num_of_workers, num_of_tasks, num_of_choices, task_capacity, dei_wbt, assign_scheme_tbw, completed_tasks, truths, expertise_truths, difficulty_truths)
    print "after prescan completed: ", completed_tasks
    if len(available_workers) != 0 and len(completed_tasks) < num_of_tasks:
        start_first_fit(num_of_workers, num_of_tasks, num_of_choices, task_capacity, dei_wbt, assign_scheme_tbw, completed_tasks, available_workers, truths, expertise_truths, difficulty_truths)

def assign_to_best_open(worker, dei_wbt, open_tasks, assign_scheme_tbw, available_workers, remain_capacity_wbt, num_of_choices, truths, expertise_truths, difficulty_truths):
    min = 1000
    min_task = -1
    for task in open_tasks:
        current = dei_wbt[worker][task]
        if current >= 0 and current < min:
            min = current
            min_task = task
    if min_task != -1:
        process_assignment(worker, task, num_of_choices, assign_scheme_tbw, available_workers, dei_wbt, remain_capacity_wbt, truths, expertise_truths, difficulty_truths)
        return True
    return False


def start_best_fit(num_of_workers, num_of_tasks, num_of_choices, task_capacity, dei_wbt, assign_scheme_tbw, completed_tasks, available_workers, truths, expertise_truths, difficulty_truths):
    remain_capacity_wbt = np.subtract(task_capacity,dei_wbt)  # after prescan, available_worker have "positive" dei over all non-completed tasks
    open_tasks = []
    assign_first_open(num_of_workers, num_of_tasks, num_of_choices, dei_wbt, remain_capacity_wbt, assign_scheme_tbw,completed_tasks, available_workers, open_tasks, truths, expertise_truths, difficulty_truths)
    for worker in available_workers:
        if assign_to_best_open(worker, dei_wbt, open_tasks, assign_scheme_tbw, available_workers,remain_capacity_wbt, num_of_choices, truths, expertise_truths, difficulty_truths) is False:
            # 1. open next open
            # 2. no tasks suitable (haven't considered, #open task = #tasks, may assign with smallest exceeding capacity )
            if len(open_tasks) < num_of_tasks:
                assign_to_closed(worker, num_of_tasks, dei_wbt, remain_capacity_wbt, assign_scheme_tbw, completed_tasks, available_workers, open_tasks, num_of_choices, truths, expertise_truths,difficulty_truths)
            else:
                pass  # 2. no tasks suitable (haven't considered, #open task = #tasks, may assign with smallest exceeding capacity )
                # assign_to_random_open
                process_assignment(worker, open_tasks[0], num_of_choices, assign_scheme_tbw, available_workers, dei_wbt, remain_capacity_wbt,truths, expertise_truths, difficulty_truths)


def best_fit_greedy(num_of_workers, num_of_tasks, num_of_choices, task_capacity, dei_wbt, assign_scheme_tbw, completed_tasks, truths, expertise_truths, difficulty_truths):
    available_workers = prescan(num_of_workers, num_of_tasks, num_of_choices, task_capacity, dei_wbt, assign_scheme_tbw,completed_tasks, truths, expertise_truths, difficulty_truths)
    if len(available_workers) != 0 and len(completed_tasks) < num_of_tasks:
        start_best_fit(num_of_workers, num_of_tasks, num_of_choices, task_capacity, dei_wbt, assign_scheme_tbw, completed_tasks, available_workers, truths, expertise_truths, difficulty_truths)


def assign_with_mode(assign_mode, num_of_workers, num_of_tasks, num_of_choices, task_capacity, dei_wbt, assign_scheme_tbw, completed_tasks, truths, expertise_truths, difficulty_truths): # cold start
    if assign_mode is "random":
        random_assign(num_of_workers, num_of_tasks, num_of_choices, assign_scheme_tbw, completed_tasks, truths, expertise_truths, difficulty_truths)

    elif assign_mode is "baseline":
        pass

    elif assign_mode is "firstfit":
        first_fit_greedy(num_of_workers, num_of_tasks, num_of_choices, task_capacity, dei_wbt, assign_scheme_tbw, completed_tasks, truths, expertise_truths, difficulty_truths)

    elif assign_mode is "bestfit":
        best_fit_greedy(num_of_workers, num_of_tasks, num_of_choices, task_capacity, dei_wbt, assign_scheme_tbw, completed_tasks, truths, expertise_truths, difficulty_truths)


def calculate_prob_ans_wbt(prob_ans_eq_truth_wbt, infer_confidence, num_of_workers, num_of_tasks, num_of_choices):
    #check element of infer_confidence should be of 1 x tasks
    prob_ans_neq_truth_wbt = (1 - prob_ans_eq_truth_wbt)/(num_of_choices - 1)
    # worker selection probability
    prob_ans_wbt = [np.zeros((num_of_workers, num_of_tasks)) for _ in range(num_of_choices)]
    prob_ans_wbt[0] = prob_ans_eq_truth_wbt * np.asarray(infer_confidence[0]) + prob_ans_neq_truth_wbt * np.asarray(infer_confidence[1])
    prob_ans_wbt[1] = prob_ans_neq_truth_wbt * np.asarray(infer_confidence[0]) + prob_ans_eq_truth_wbt * np.asarray(infer_confidence[1])

    return prob_ans_wbt


def calculate_ei(infer_confidence_score, infer_confidence, infer_expertise_score, infer_difficulty, estimated_difficulty_score, num_of_workers, num_of_tasks, num_of_choices):
    #infer_expertise_score and infer_difficulty are "1 x tasks"
    ei_wbt = [np.zeros((num_of_workers, num_of_tasks)) for _ in range(num_of_choices)]
    updated_confidence_score = [np.zeros((num_of_workers, num_of_tasks)) for _ in range(num_of_choices)]
    updated_dampen_confidence_score = [np.zeros((num_of_workers, num_of_tasks)) for _ in range(num_of_choices)]
    updated_confidence = [np.zeros((num_of_workers, num_of_tasks)) for _ in range(num_of_choices)]
    updated_difficulty_score = [np.zeros((num_of_workers, num_of_tasks)) for _ in range(num_of_choices)]
    for i in range(num_of_choices):
        updated_confidence_score[i] = np.add(np.asarray([infer_confidence_score[i],] * num_of_workers), np.asarray(infer_expertise_score)[:,None]) # wbt # have to add dampen factors
    updated_dampen_confidence_score[0] = updated_confidence_score[0] - updated_confidence_score[1]
    updated_dampen_confidence_score[1] = updated_confidence_score[1] - updated_confidence_score[0]

    for i in range(num_of_choices):
        updated_confidence[i] = (1/(1 + np.power(math.e, -updated_dampen_confidence_score[i]))) * np.asarray(infer_difficulty) #make sure the infer/update confidence have the same difficulties
        if i is 0:
            updated_difficulty_score[i] = np.abs(np.subtract(np.asarray(updated_confidence[i]),np.asarray(infer_confidence[1])))
        elif i is 1:
            updated_difficulty_score[i] = np.abs(np.subtract(updated_confidence[i],infer_confidence[0]))

        ei_wbt[i] = np.subtract(updated_difficulty_score[i],estimated_difficulty_score)
    return ei_wbt


def calculate_dei(num_of_workers, num_of_tasks, num_of_choices, infer_expertise, infer_expertise_score, infer_difficulty, estimated_difficulty_score, infer_confidence, infer_confidence_score):
    # infer_confidence_score is 2 x tasks, infer_expertise_score is 1 x workers
    prob = np.transpose(np.multiply(np.asarray(infer_expertise), np.asarray(infer_difficulty)[:, None]))
    prob_ans_eq_truth_wbt = 1 / (1 + np.power(math.e, -3 * prob))
    prob_ans_wbt = calculate_prob_ans_wbt(prob_ans_eq_truth_wbt, infer_confidence, num_of_workers, num_of_tasks, num_of_choices)
    ei_wbt = calculate_ei(infer_confidence_score, infer_confidence, infer_expertise_score, infer_difficulty, estimated_difficulty_score, num_of_workers, num_of_tasks, num_of_choices)
    dei_wbt = np.abs(np.add(np.multiply(prob_ans_wbt[0],ei_wbt[0]),np.multiply(prob_ans_wbt[1],ei_wbt[1]))) # should be abs
    return dei_wbt


def start_inference(num_of_workers, num_of_tasks, num_of_choices, assign_scheme_tbw, expertise_init, difficulty_init):
    # return model paras

    # start learning
    [expertise, difficulty] = init(num_of_workers, expertise_init, num_of_tasks, difficulty_init)
    for iter_all in range(5): # whole process
        for iter_left in range(5): # left cycle
            # expertise should be value of last iteration
            expertise_score = [-np.log(1 - x) for x in expertise]
            confidence_score = [np.dot(x, expertise_score) for x in assign_scheme_tbw]
            confidence_score_damping = np.zeros((num_of_choices, num_of_tasks))
            confidence = np.zeros((num_of_choices, num_of_tasks))

            confidence_score_damping[0][:] = confidence_score[0][:] - 1 * confidence_score[1][:]
            confidence_score_damping[1][:] = confidence_score[1][:] - 1 * confidence_score[0][:]

            for task in range(num_of_tasks):
                for choice in range(num_of_choices):
                    confidence[choice][task] = difficulty[task] * (1 / (1 + np.power(math.e, -confidence_score_damping[choice][task])))
                    # confidence[choice][task] = 1 / (1 + np.power(math.e, -confidence_score_damping[choice][task]))

            confidence = confidence / confidence.sum(axis=0) # normalize confidence
            for x in range(num_of_workers):
                expertise[x] = 0
                for task in range(num_of_tasks):
                    for choice in range(num_of_choices):
                        expertise[x] += assign_scheme_tbw[choice][task][x] * confidence[choice][task]
            expertise = [x / num_of_tasks for x in expertise]

        difficulty_score = np.zeros(num_of_tasks)
        for iter_right in range(3):  # right cycle
            for task in range(num_of_tasks):
                difficulty_score[task] = np.abs(confidence[0][task] - confidence[1][task])
                difficulty[task] = 1 / (1 + 0.4 * np.power(math.e, -difficulty_score[task]))
            # update confidence
            for task in range(num_of_tasks):
                for choice in range(num_of_choices):
                    confidence[choice][task] = difficulty[task] * (1 / (1 + np.power(math.e, -confidence_score_damping[choice][task])))

            confidence = confidence / confidence.sum(axis=0)  # normalize confidence
        # update expertise
        for x in range(num_of_workers):
            expertise[x] = 0
            for task in range(num_of_tasks):
                for choice in range(num_of_choices):
                    expertise[x] += assign_scheme_tbw[choice][task][x] * confidence[choice][task]
        expertise = [x / num_of_tasks for x in expertise]
    return [expertise, expertise_score, confidence, confidence_score, difficulty, difficulty_score] #check whether local can return


def process_completed_tasks(num_of_tasks, threshold, infer_difficulty_score, infer_confidence, completed_tasks, infer_truths):
    for i in range(num_of_tasks):
        if i in completed_tasks and infer_truths[i] == 0:
            infer_truths[i] = 1 if infer_confidence[0][i] > infer_confidence[1][i] else 2
        if i not in completed_tasks and infer_difficulty_score[i] >= threshold:
            infer_truths[i] = 1 if infer_confidence[0][i] > infer_confidence[1][i] else 2
            completed_tasks.append(i)

    for i in range(num_of_tasks):
        if i not in completed_tasks:
            print "task ", i, " has inferred difficulty score: ", infer_difficulty_score[i], " has confidence: ", infer_confidence[0][i], " and ", infer_confidence[1][i]


def print_accuracy(num_of_tasks, truths, infer_truths):
    # accuracy = (num_of_tasks - np.count_nonzero(np.subtract(truths, infer_truths)))/float(num_of_tasks)
    return (num_of_tasks - np.count_nonzero(np.subtract(truths, infer_truths)))


def synthetic_exp(assign_mode, max_number_of_workers, worker_arri_rate, num_of_tasks, num_of_choices, expertise_init, difficulty_init, confidence_init, threshold):
    num_of_workers = 0
    infer_expertise = []
    infer_expertise_score = []
    infer_confidence = [[confidence_init] * num_of_tasks for _ in range(num_of_choices)]
    infer_confidence_score = [ np.zeros(num_of_tasks) for _ in range(num_of_choices)]
    infer_difficulty = [difficulty_init] * num_of_tasks
    infer_difficulty_score = np.zeros(num_of_tasks)
    truths = tasks_generator(num_of_tasks, num_of_choices) # 1 x tasks
    difficulty_truths = [uniform_random_generator(0.8,1)] * num_of_tasks
    expertise_truths = []
    infer_truths = np.zeros(num_of_tasks)
    completed_tasks = []
    time = 0
    while(len(completed_tasks) < num_of_tasks): #begin a batch, old workers/tasks: last batch paras, new workers/tasks: initialized
        # print #completed tasks as the potentially completed questions
        # num_of_workers += worker_arri_rate if num_of_workers < max_number_of_workers else 1 # control the max numer of workers
        print "_________________________iteration_________________________: ", time
        process_completed_tasks(num_of_tasks, threshold, infer_difficulty_score, infer_confidence, completed_tasks,infer_truths)  # check whether completed tasks are updated
        print "_________________________completed tasks after processing:", completed_tasks
        print "_________________________#completes: ", len(completed_tasks)
        num_of_workers += worker_arri_rate
        if num_of_workers == worker_arri_rate:
            assign_scheme_tbw = [np.zeros((num_of_tasks, num_of_workers)) for _ in range(num_of_choices)]  # assignmnet scheme
        else:
            assign_scheme_tbw = [np.hstack((assign_scheme_tbw[i], np.zeros((num_of_tasks, worker_arri_rate)))) for i in range(num_of_choices)]

        expertise_truths = expertise_truths + [uniform_random_generator(0.5, 0.999)] * worker_arri_rate

        infer_expertise = infer_expertise + [expertise_init] * worker_arri_rate
        infer_expertise_score = infer_expertise_score + [-np.log(1-expertise_init)] * worker_arri_rate
        estimated_difficulty_score = np.abs(np.subtract(np.asarray(infer_confidence[0]), np.asarray(infer_confidence[1])))
        task_capacity = threshold - estimated_difficulty_score #threshold can be vector or scala
        dei_wbt = calculate_dei(num_of_workers, num_of_tasks, num_of_choices, infer_expertise, infer_expertise_score,
                                                infer_difficulty, estimated_difficulty_score, infer_confidence, infer_confidence_score)

        # consider task processing time, should add an available worker set, check whether assign_scheme_tbw is changed
        assign_with_mode(assign_mode, num_of_workers, num_of_tasks, num_of_choices, task_capacity, dei_wbt, assign_scheme_tbw, completed_tasks, truths, expertise_truths, difficulty_truths) # assign_scheme_tbw includes the answers
        [infer_expertise, infer_expertise_score, infer_confidence, infer_confidence_score, infer_difficulty, infer_difficulty_score] = start_inference(num_of_workers, num_of_tasks, num_of_choices, assign_scheme_tbw,expertise_init, difficulty_init)
        # process_completed_tasks(num_of_tasks, threshold, infer_difficulty_score, infer_confidence, completed_tasks, infer_truths)  # check whether completed tasks are updated
        # print "process completed:", completed_tasks
        time += 1
    return [print_accuracy(num_of_tasks, truths, infer_truths), time]


num_of_tasks = 15
worker_arri_rate = 1
num_of_choices = 2
threshold = 0.4
expertise_init = 0.5
difficulty_init = 0.5
confidence_init = 0.5
max_number_of_workers = 50
accuracy_ff = 0
time_ff = 0
iteration = 5

def main(assign_mode):
    accuracy_ff = 0
    time_ff = 0
    for ite in range(iteration):
        [accuracy, time] = synthetic_exp(assign_mode, max_number_of_workers, worker_arri_rate, num_of_tasks, num_of_choices, expertise_init, difficulty_init, confidence_init, threshold)
        accuracy_ff += accuracy
        time_ff += time
    print assign_mode, ": "
    print " accuracy: ", 100*float(accuracy_ff)/(iteration * num_of_tasks), "%"
    print " time: ", float(time_ff)/iteration

main("random")
# main("firstfit")
# main("bestfit")